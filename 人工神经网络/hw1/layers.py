import numpy as np

_debug = False

def setDebug(on):
    global _debug
    _debug = on

class Layer(object):
    def __init__(self, name, trainable=False):
        self.name = name
        self.trainable = trainable
        self._saved_tensor = None

    def __str__(self):
        return "BaseLayer: " + self.name

    def forward(self, input):
        pass

    def backward(self, grad_output):
        pass

    def update(self, config):
        pass

    def _saved_for_backward(self, tensor):
        '''The intermediate results computed during forward stage
        can be saved and reused for backward, for saving computation'''

        self._saved_tensor = tensor


class Relu(Layer):
    def __init__(self, name):
        super(Relu, self).__init__(name)

    def __str__(self):
        return "Relu: " + self.name

    def forward(self, input):
        self._saved_for_backward(input)
        return np.maximum(input, 0)

    def backward(self, grad_output):
        grad_output[self._saved_tensor <= 0] = 0
        return grad_output


class Sigmoid(Layer):
    def __init__(self, name):
        super(Sigmoid, self).__init__(name)

    def __str__(self):
        return "Sigmoid: " + self.name

    def forward(self, input):
        res = 1. / (1. + np.exp(-input))
        self._saved_for_backward(res)
        return res

    def backward(self, grad_output):
        return grad_output * self._saved_tensor * (1. - self._saved_tensor)


class Linear(Layer):
    def __init__(self, name, in_num, out_num, init_std):
        super(Linear, self).__init__(name, trainable=True)
        self.in_num = in_num
        self.out_num = out_num
        self.W = np.random.randn(in_num, out_num) * init_std
        self.b = np.zeros(out_num)

        self.grad_W = np.zeros((in_num, out_num))
        self.grad_b = np.zeros(out_num)

        self.diff_W = np.zeros((in_num, out_num))
        self.diff_b = np.zeros(out_num)

    def __str__(self):
        return "Linear: " + self.name + ", (?,{},{})".format(self.in_num, self.out_num)

    def forward(self, input):
        self._saved_for_backward(input)
        return input.dot(self.W) + self.b

    def backward(self, grad_output):
        self.grad_W = self._saved_tensor.T.dot(grad_output)
        self.grad_b = grad_output.sum(axis=0)
        return grad_output.dot(self.W.T)

    def update(self, config):
        mm = config['momentum']
        lr = config['learning_rate']
        wd = config['weight_decay']
        if(_debug):
            print(str(self) + ": L2-norm of gradient is {}".format(np.linalg.norm(self.grad_W, ord=2)))
        self.diff_W = mm * self.diff_W + (self.grad_W + wd * self.W)
        self.W = self.W - lr * self.diff_W
        self.diff_b = mm * self.diff_b + (self.grad_b + wd * self.b)
        self.b = self.b - lr * self.diff_b
"""
More complicated test examples.
"""
from numpy.testing import *
from numpy.testing.decorators import *
import numpy

from algopy import *
from algopy.linalg import *

class Test_MaximimLikelihoodExample(TestCase):

    def transform_params(self, Y):
        X = exp(Y)
        tsrate, tvrate = X[0], X[1]
        v_unnormalized = zeros(4, dtype=X)
        v_unnormalized[0] = X[2]
        v_unnormalized[1] = X[3]
        v_unnormalized[2] = X[4]
        v_unnormalized[3] = 1.0
        v = v_unnormalized / sum(v_unnormalized)
        return tsrate, tvrate, v

    def eval_f(self, Y):
        """
        using algopy.expm
        """

        a, b, v = self.transform_params(Y)

        g_data = numpy.array([
                [2954, 141, 17, 16],
                [165, 1110, 5, 2],
                [18, 4, 3163, 374],
                [15, 2, 310, 2411],
                ],dtype=float)


        Q = zeros((4,4), dtype=Y)
        Q[0,0] = 0;    Q[0,1] = a;    Q[0,2] = b;    Q[0,3] = b;
        Q[1,0] = a;    Q[1,1] = 0;    Q[1,2] = b;    Q[1,3] = b;
        Q[2,0] = b;    Q[2,1] = b;    Q[2,2] = 0;    Q[2,3] = a;
        Q[3,0] = b;    Q[3,1] = b;    Q[3,2] = a;    Q[3,3] = 0;

        Q = Q * v
        Q -= diag(sum(Q, axis=1))
        P = expm(Q)
        S = log(dot(diag(v), P))
        return -sum(S * g_data)

    def eval_f_eigh(self, Y):
        """
        reformulation of eval_f(Y) to use eigh instead of expm
        """

        a, b, v = self.transform_params(Y)

        g_data = numpy.array([
                [2954, 141, 17, 16],
                [165, 1110, 5, 2],
                [18, 4, 3163, 374],
                [15, 2, 310, 2411],
                ],dtype=float)


        Q = zeros((4,4), dtype=Y)
        Q[0,0] = 0;    Q[0,1] = a;    Q[0,2] = b;    Q[0,3] = b;
        Q[1,0] = a;    Q[1,1] = 0;    Q[1,2] = b;    Q[1,3] = b;
        Q[2,0] = b;    Q[2,1] = b;    Q[2,2] = 0;    Q[2,3] = a;
        Q[3,0] = b;    Q[3,1] = b;    Q[3,2] = a;    Q[3,3] = 0;

        Q = dot(Q, diag(v))
        Q -= diag(sum(Q, axis=1))
        va = diag(sqrt(v))
        vb = diag(1./sqrt(v))
        W, U = eigh(dot(dot(va, Q), vb))
        M = dot(U, dot(diag(exp(W)), U.T))
        P = dot(vb, dot(M, va))
        S = log(dot(diag(v), P))
        return -sum(S * g_data)


    def eval_grad_f_eigh(self, Y):
        """
        compute the gradient of f in the forward mode of AD
        """
        Y = UTPM.init_jacobian(Y)
        retval = self.eval_f_eigh(Y)
        return UTPM.extract_jacobian(retval)

    def eval_hess_f_eigh(self, Y):
        """
        compute the hessian of f in the forward mode of AD
        """
        Y = UTPM.init_hessian(Y)
        retval = self.eval_f_eigh(Y)
        hessian = UTPM.extract_hessian(5, retval)
        return hessian

    def eval_grad_f(self, Y):
        """
        compute the gradient of f in the forward mode of AD
        """
        Y = UTPM.init_jacobian(Y)
        retval = self.eval_f(Y)
        return UTPM.extract_jacobian(retval)

    def eval_hess_f(self, Y):
        """
        compute the hessian of f in the forward mode of AD
        """
        Y = UTPM.init_hessian(Y)
        retval = self.eval_f(Y)
        hessian = UTPM.extract_hessian(5, retval)
        return hessian

    def test_expm_implementations(self):
        """
        Check for syntax errors within the expm Pade approximations.
        """

        Y = numpy.zeros(5)

        a, b, v = self.transform_params(Y)

        Q = zeros((4,4), dtype=Y)
        Q[0,0] = 0;    Q[0,1] = a;    Q[0,2] = b;    Q[0,3] = b;
        Q[1,0] = a;    Q[1,1] = 0;    Q[1,2] = b;    Q[1,3] = b;
        Q[2,0] = b;    Q[2,1] = b;    Q[2,2] = 0;    Q[2,3] = a;
        Q[3,0] = b;    Q[3,1] = b;    Q[3,2] = a;    Q[3,3] = 0;

        Q = Q * v
        Q -= diag(sum(Q, axis=1))

        # Pade approximations of explicit order.
        for q in (3, 5, 7, 9, 13):
            expm_pade(Q, q)

        # Squaring and scaling on top of Pade approximations.
        expm_higham_2005(Q)

        # Default expm implementation.
        expm(Q)



    def test_ml_with_expm_gradient_forward(self):

        Y = numpy.zeros(5)

        assert_array_almost_equal(self.eval_f_eigh(Y), self.eval_f(Y))
        assert_array_almost_equal(self.eval_grad_f_eigh(Y), self.eval_grad_f(Y))

    def test_ml_with_expm_hessian_forward(self):

        Y = numpy.zeros(5)
        assert_array_almost_equal(self.eval_f_eigh(Y), self.eval_f(Y))
        assert_array_almost_equal(self.eval_hess_f_eigh(Y), self.eval_hess_f(Y))



    @knownfailureif(numpy.__version__[:3] != 1.4, msg = " this test fails at Q = Q * v because of the numpy broadcasting bug")
    def test_ml_with_expm_gradient_reverse(self):
        # test reverse mode

        cg = CGraph()
        x = Function(Y)
        y = self.eval_f_eigh(x)
        cg.independentFunctionList = [x]
        cg.dependentFunctionList = [y]

        g1 = self.eval_grad_f(Y)
        g2 = cg.gradient(Y)

        assert_array_almost_equal(g1, g2)


class Test_OdoeExample(TestCase):

    def test_objective_function(self):

        def Cfcn(F1p_list, out = None, work = None):
            from numpy import sum, zeros
            from algopy import inv, dot, zeros

            # check input arguments
            Nex  = len(F1p_list)
            Np   = F1p_list[0].shape[1]

            # create temporary matrix M if not provided
            # to store M = [[J_1^T J_1, J_2^T],[J_2, 0]]
            if work == None:
                work = zeros((Np,Np), dtype=F1p_list[0])
            M = work

            # Step 1:   compute M = J_1^T J_1
            for nex in range(Nex):
                M += dot(F1p_list[nex].T, F1p_list[nex])

            # Step 2: invert M and prepare output

            if out == None:
                out = inv(M)
            else:
                out[...] = M
            return out

        D,P,N,M = 2,1,100,3
        F1p_list = [UTPM(numpy.random.rand(D,P,N,M)),UTPM(numpy.random.rand(D,P,N,M))]
        cg = CGraph()
        FF1p_list = [Function(F1p) for F1p in F1p_list]
        FC = Cfcn(FF1p_list)
        FPHI = Function.trace(FC)

        cg.independentFunctionList = FF1p_list
        cg.dependentFunctionList = [FPHI]

        assert_array_equal(FPHI.shape, ())
        # cg.pushforward(F1p_list)
        PHIbar = UTPM(numpy.zeros((D,P)))
        PHIbar.data[0,:] = 1.

        # pullback using the tracer
        cg.pullback([PHIbar])

        # verifying the computation
        const1 =  UTPM.dot(PHIbar, UTPM.shift(FPHI.x,-1))
        # print const1

        Cbar = UTPM.pb_trace(PHIbar, FC.x, FPHI.x)
        assert_array_almost_equal(Cbar.data, FC.xbar.data)
        const2 =  UTPM.trace(UTPM.dot(Cbar.T, UTPM.shift(FC.x,-1)))
        # print const2

        const3 = UTPM(numpy.zeros((D,P)))

        for nFF1p, FF1p in enumerate(FF1p_list):
            const3 += UTPM.trace(UTPM.dot(FF1p.xbar.T, UTPM.shift(FF1p.x,-1)))

        # print const3

        assert_array_almost_equal(const1.data[0,:], const2.data[0,:])
        assert_array_almost_equal(const2.data[0,:], const3.data[0,:])















if __name__ == "__main__":
    run_module_suite()




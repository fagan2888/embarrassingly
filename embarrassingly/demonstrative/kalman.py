import math
import numpy as np
from scipy.optimize import shgo
from embarrassingly.underpromoted import Underpromoted2d
from pprint import pprint

# See https://www.microprediction.com/blog/robust-optimization for explanation of experiments


def kalman_error(xs, ys):
    """
    :param xs:   np.array with [Q, R] parameters
    :param ys:   time series observed with noise, or list of the same
    :return:
    """

    def ke(xs, ys):
        """ Kalman prediction error
              xs - params sqrt(Q), sqrt(R)  corresponding to std deviations in process, measurement noise
              ys
        """
        Q = xs[0]*xs[0]
        R = xs[1]*xs[1]
        x = ys[0]
        P = Q
        errors = list()
        for yi in ys:
            y_hat = x
            errors.append(yi-y_hat)
            dy = yi-y_hat
            P = P + Q
            K = P / (P + R)
            x = x + K * dy
            P = (1 - K) * P
        return math.sqrt( np.mean( np.array(errors)**2 ) )

    return ke(xs=xs,ys=ys)


def in_sample_kalman_error(xs, ys):
    if len(ys)>500:
        return kalman_error(xs=xs, ys=ys[:50])
    else:
        return 0.0


def out_of_sample_kalman_error(xs, ys):
    if len(ys)>=750:
        return kalman_error(xs=xs, ys=ys[50:])
    else:
        return 0.0


def robust_fit_out_of_sample_error(xs, ys, bounds, verbose=False)->float:
    errs = robust_fit_out_of_sample_error_report(xs=xs, ys=ys, bounds=bounds, verbose=verbose)
    return float(np.mean(np.mean(errs)))


def robust_fit_out_of_sample_error_report(xs, ys, bounds, verbose=False)->[[float]]:
    """ Find best radius and kappa
    :param xs:          [ radius, kappa ]
    :param ys:    time series, or list of time series
    :param bounds:
    :param verbose:
    :return:
    """
    radius = math.exp(xs[0])
    kappa = math.exp(xs[1])

    if isinstance(ys[0], list):
        all_ys = ys
    else:
        all_ys = [ys]

    all_errs = list()
    for ys in all_ys:
        ftol = 0.0001
        n = 25
        iters = 5
        # Without underpromotion ...
        res = shgo(func=in_sample_kalman_error, bounds=bounds, args=(ys,), n=n, iters=iters,
                   options={'minimize_every_iter': True, 'ftol': ftol})
        in_sample_error = in_sample_kalman_error(res.x, ys)
        out_sample_error = out_of_sample_kalman_error(res.x, ys)
        # With underpromotion
        in_sample_tilde = Underpromoted2d(in_sample_kalman_error, radius=radius, kappa=kappa, bounds=bounds, func_kwargs={'ys':ys})
        in_sample_tilde.verbose = False
        res1 = shgo(func=in_sample_tilde, bounds=bounds, n=n, iters=iters, options={'minimize_every_iter': True, 'ftol': ftol})
        in_sample_error_tilde = in_sample_kalman_error(res1.x, ys)
        out_sample_error_tilde = out_of_sample_kalman_error(res1.x, ys)
        errs = [ [in_sample_error, out_sample_error],[in_sample_error_tilde,out_sample_error_tilde]]
        all_errs.append(errs)
    if verbose:
        print(errs)
    return all_errs

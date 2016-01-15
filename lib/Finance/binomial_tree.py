"""
    Module: Calculate the option price for 1-step binomial tree
    Parameters are s_u, s_d, X, T, rf and s.
    X: Strike price of the option
    T: Maturity
    Module returns f.

    Author: Peter Lee

    Date: 02-Dec-2015

    Notes:
    risk-free rate: rf

    T=0                            T=1

                               s_u    f_u
    s, f
                               s_d    f_d

    Assumptions: Risk-neutral valuation (riskless portfolio earns the risk-free rate).
"""


import numpy as np

def binomial_tree_1_branch(s=10, s_u=11, s_d=9, x=10.5, t=0.25, rf=0.12):
    """
    Module: Calculate the option price for 1-step binomial tree
    Parameters are s_u, s_d, X, T, rf and s.
    s: Asset price at T=0
    s_u: Asset price at T=1 if price increases
    s_d: Asset price at T=1 if price decreases
    x: Stike price of the option
    t: Maturity of the option (in years)
    rf: Risk free rate (p.a. e.g. 0.12)
    Module returns f: the option price at T=0.
    Portfolio: Long Delta assets while short an option
    """

    # Find P
    p = ( s*np.exp(rf*t) - s_d ) / (s_u - s_d)

    # Find f
    f_u = np.max((0, s_u - x))
    f_d = np.max((0, s_d - x))
    f = ( p*f_u + (1 - p)*f_d ) * np.exp( - rf*t )

    print("Parameters are: S={s}, S_u={s_u}, S_d={s_d}, X={x}, T={t}, Rf={rf}.".format(s=s, s_u=s_u, s_d=s_d, x=x, t=t, rf=rf))
    print("Option price f = {f}, with probability of up-move p = {p}, f_u={f_u}, f_d={f_d}".format(f=f, p=p, f_u=f_u, f_d=f_d))


def binomial_tree_european(price=20, 
                  volatility=0.3,
                  rf=0.05,
                  t=1,
                  x=21,
                  steps=2,
                  call_or_put='call',
                  american=False):
    """
    Return the option price using a n-step binomial tree.

    Parameters:
        price: price of the stock at t=0;
        volatility: i.e. 30% is expressed as 0.3; the volatility of the stock price series, or the standard deviation of return times the square root of delta t.
        rf: the risk free rate p.a.
        t: the time expiry of the option
        x: the strike price
        steps: number of steps in the binomial tree
        call_or_put: Takes the value of 'call' or 'put'; defaulted to 'call'.
        american: True if American option, False if European option.


    Formulas:
        Assumed generating the binomial tree by matching the volatility of the stock prices:
        The up move factor:
            u = exp( sigma*sqrt(delta t) )
        The down move factor:
            d = exp( - sigma*sqrt(delta t) )

        The probability of an up-move:
            p = ( exp( rf*delta t ) - d ) / ( u - d )
    """

    # Key variables
    delta_t = t/steps
    u = np.exp( volatility*np.sqrt(delta_t) )
    d = np.exp( - volatility*np.sqrt(delta_t) )
    p = ( np.exp(rf*delta_t) - d ) / (u - d)
    print("delta_t is {}, u = {}, d = {}, p = {}".format(delta_t, u, d, p))

    # Generating all end nodes
    end_nodes = []
    f = 0 # Option price
    for i in range(0, steps + 1):
        s_t = price*u**(steps - i)*( d**i )
        if call_or_put=='call':
            f_t = np.max([s_t-x, 0])
        else:
            f_t = np.max([x-s_t, 0])

        end_nodes.append((s_t, f_t))
        f += p**(steps - i) * (1-p)**(i) * f_t
        
        print("s_t = price*p^({})*( (1-p)^({}) )".format(steps-i, i))
        print('f is  {}'.format(f))

    return f
        

def node_price(price, n_up, n_down, u, d):
    """
    Find the price of n_up up-moves; and m_down down-moves;
    price: beginning stock price
    n_up: number of up-moves
    n_down: number of down_moves
    u: the up factor
    d: the down factor
    """
    node_price = price * u**n_up * d**n_down
    return node_price

def binomial_tree(k=0,
                  n_up=0,
                  price=20, 
                  volatility=0.3,
                  rf=0.05,
                  t=1,
                  x=21,
                  steps=2,
                  call_or_put='call',
                  american=False):
    """
    Return the option price using a n-step binomial tree at k-th level of decision node with n-up up-movements.

    Parameters:
        k: the level of decision nodes (number of paths since t=0)
        n_up: among the k paths, the number of up-movements.
        price: price of the stock at t=0;
        volatility: i.e. 30% is expressed as 0.3; the volatility of the stock price series, or the standard deviation of return times the square root of delta t.
        rf: the risk free rate p.a.
        t: the time expiry of the option
        x: the strike price
        steps: number of steps in the binomial tree
        call_or_put: Takes the value of 'call' or 'put'; defaulted to 'call'.
        american: True if American option, False if European option.


    Formulas:
        Assumed generating the binomial tree by matching the volatility of the stock prices:
        The up move factor:
            u = exp( sigma*sqrt(delta t) )
        The down move factor:
            d = exp( - sigma*sqrt(delta t) )

        The probability of an up-move:
            p = ( exp( rf*delta t ) - d ) / ( u - d )
    """
    delta_t = t/steps
    u = np.exp( volatility*np.sqrt(delta_t) )
    d = np.exp( - volatility*np.sqrt(delta_t) )
    p = ( np.exp(rf*delta_t) - d ) / (u - d)
 
    n_down = k - n_up
    node_p = node_price(price, n_up, n_down, u, d)

    if call_or_put==True:
        node_f = np.max((0, node_p - x))
    else:
        node_f = np.max((0, x - node_p))

    if k==steps: 
        # end nodes
        return node_f

    # Using forward induction to find intermediate nodes
    expected_node_f_fv = p * binomial_tree(k + 1, n_up + 1, price, volatility, rf, t, x, steps, call_or_put, american) +\
                      (1 - p) * binomial_tree(k + 1, n_up, price, volatility, rf, t, x, steps, call_or_put, american)
    expected_node_f = expected_node_f_fv*np.exp( -rf*delta_t )

    if american==True:
        return np.max((expected_node_f, node_f))
    else:
        return expected_node_f


if __name__=="__main__":
    f = binomial_tree(k=0,
                  n_up=0,
                  price=50,
                  volatility=0.3,
                  rf=0.05,
                  t=2,
                  x=52,
                  steps=2,
                  call_or_put='put',
                  american=True)
    print("The option price is: ${:.3f}".format(f))



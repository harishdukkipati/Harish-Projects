"""
Analysis question.
Change these default values to obtain the specified policies through value iteration.
If any question is not possible, return just the constant NOT_POSSIBLE:
```
return NOT_POSSIBLE
```
"""

NOT_POSSIBLE = None

def question2():
    """
    Lowering the noise paramater allowed the agent to be more focused
    and as a result crossed the bridge
    """
    answerDiscount = 0.9
    answerNoise = 0.01

    return answerDiscount, answerNoise

def question3a():
    """
    [Enter a description of what you did here.]
    Lowering noise so that it's more prone to error(risking cliff)
    Lower discount factor for immediate rewards
    Lower the living rewards for distant exit so it chooses closer
    exit
    """
    answerDiscount = .5
    answerNoise = .01
    answerLivingReward = -1.1

    return answerDiscount, answerNoise, answerLivingReward

def question3b():
    """
    Lower the discount factor in order to prioritize the immediate rewards
    Lower the living rewards for distant exit so it chooses closer
    exit
    """

    answerDiscount = 0.5
    answerNoise = 0.2
    answerLivingReward = -1.0

    return answerDiscount, answerNoise, answerLivingReward

def question3c():
    """
    Lowers the noise so that it risks the cliff by not avoiding it
    """

    answerDiscount = 0.7
    answerNoise = 0.09
    answerLivingReward = 0.0

    return answerDiscount, answerNoise, answerLivingReward

def question3d():
    """
    Higher answer discount and non-negative living reward
    prioritizes choosing distant exit. Increasing noise
    allows it to avoid the cliff
    """

    answerDiscount = 0.9
    answerNoise = 0.3
    answerLivingReward = 0.0

    return answerDiscount, answerNoise, answerLivingReward

def question3e():
    """
    Decreased the answerLivingReward to 0 so that it avoids the cliff
    but also lower the answerDiscount so it doesn't choose any exit.
    """
    answerDiscount = 0.3
    answerNoise = 0.3
    answerLivingReward = 0.0

    return answerDiscount, answerNoise, answerLivingReward

def question6():
    """
    Optimal Policy can't be learned within 50 iterations
    """
    return NOT_POSSIBLE

if __name__ == '__main__':
    questions = [
        question2,
        question3a,
        question3b,
        question3c,
        question3d,
        question3e,
        question6,
    ]

    print('Answers to analysis questions:')
    for question in questions:
        response = question()
        print('    Question %-10s:\t%s' % (question.__name__, str(response)))

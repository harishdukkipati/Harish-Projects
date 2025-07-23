import math


def unigram_data(word_counts, remove):
    """
    Processes the training data to compute unigram word counts and handles out-of-vocabulary (OOV) words.

    Args:
        word_counts (dict): Dictionary to store word counts.
        remove (list): List to store words to be removed (words occurring less than three times).

    """
    with open("1b_benchmark.train.tokens", "r", encoding="utf8") as train:
        for line in train:
            tokens = line.split()
            tokens.insert(0, "<START>")
            tokens.append("<STOP>")

            for token in tokens:
                word_counts[token] = word_counts.get(token, 0) + 1

    word_counts["UNK"] = 0
    for word, count in word_counts.items():
        if count < 3:
            remove.append(word)
            word_counts["UNK"] += count

    for word in remove:
        del word_counts[word]


def unigram_mle(word_counts, mle_est):
    """
    Computes the Maximum Likelihood Estimation (MLE) for unigram probabilities.

    Args:
        word_counts (dict): Dictionary containing word counts.
        mle_est (dict): Dictionary to store MLE probabilities.

    """
    alpha = 1
    vocab_size = len(word_counts)
    total_words = sum(word_counts.values()) - word_counts["<START>"]
    # additive soothing
    for word, count in word_counts.items():
        if word != "<START>":
            mle_est[word] = (count + alpha) / \
                (total_words + alpha * vocab_size)
    # probability not zero if it's unkown
    mle_est["UNK"] = alpha / (total_words + alpha * vocab_size)


def unigram_perplexity(data, mle_est):
    """
    Computes the perplexity for unigram model.

    Args:
        data (list): List of sentences for evaluation.
        mle_est (dict): Dictionary containing MLE probabilities.

    Returns:
        float: Perplexity score.

    """
    sentence_total, total, sentence_len = 0, 0, 0
    for sentence in data:
        tokens = sentence.split()
        for unigram in tokens:
            if unigram == "<START>":
                continue
            sentence_total += math.log(mle_est.get(unigram, mle_est["UNK"]))
            sentence_len += 1
        total += sentence_total
        sentence_total = 0

    inverse = -1 / sentence_len
    exponent = inverse * total
    perplexity = math.exp(exponent)
    return perplexity


def ngram_data(data, num_tokens, word_counts):
    """
    Processes the data to compute n-gram word counts.

    Args:
        data (list): List of sentences.
        num_tokens (int): Number of tokens in the n-gram (2 for bigram, 3 for trigram).
        word_counts (dict): Dictionary to store n-gram counts.

    """
    for sentence in data:
        tokens = sentence.split()
        if num_tokens == 2:
            ngrams = [(tokens[i], tokens[i + 1])
                      for i in range(len(tokens) - 1)]
        elif num_tokens == 3:
            ngrams = [(tokens[i], tokens[i + 1], tokens[i + 2])
                      for i in range(len(tokens) - 2)]
        for ngram in ngrams:
            word_counts[ngram] = word_counts.get(ngram, 0) + 1


def bigram_mle(bigram, mle_est, unigram_prob):
    """
    Computes the Maximum Likelihood Estimation (MLE) for bigram probabilities.

    Args:
        bigram (tuple): Bigram tuple.
        mle_est (dict): Dictionary containing bigram counts.
        unigram_prob (dict): Dictionary containing unigram probabilities.

    Returns:
        float: Bigram probability.

    """
    # print(len(igram))
    alpha = 1  # Smoothing parameter
    first_word = bigram[0]

    if first_word in unigram_prob:
        first_word_count = unigram_prob[first_word]
    else:
        first_word_count = 0

    vocab_size = len(unigram_prob)
    if bigram in mle_est:
        bigram_count = mle_est[bigram] + alpha
    else:
        bigram_count = alpha

    smoothed_probability = bigram_count / \
        (first_word_count + alpha * vocab_size)

    return smoothed_probability


def bigram_perplexity(data, mle_est, unigram_prob):
    """
    Computes the perplexity for bigram model.

    Args:
        data (list): List of sentences for evaluation.
        mle_est (dict): Dictionary containing bigram counts.
        unigram_prob (dict): Dictionary containing unigram probabilities.

    Returns:
        float: Perplexity score.

    """
    sentence_total, total, sentence_len = 0, 0, 0
    for sentence in data:
        tokens = sentence.split()
        bigrams = [(tokens[i], tokens[i + 1]) for i in range(len(tokens) - 1)]
        for bigram in bigrams:
            if (bigram[0] == "<START>" and bigram[1] == "<START>"):
                continue
            prob = bigram_mle(bigram, mle_est, unigram_prob)
            if prob != 0:
                sentence_total += math.log(prob)
        total += sentence_total
        sentence_total = 0
        sentence_len += len(tokens) - 1

    inverse = -1 / sentence_len
    exponent = inverse * total
    perplexity = math.exp(exponent)
    return perplexity


def trigram_mle(trigram, mle_est, bigram_prob, donkey):
    """
    Computes the Maximum Likelihood Estimation (MLE) for trigram probabilities.

    Args:
        trigram (tuple): Trigram tuple.
        mle_est (dict): Dictionary containing trigram counts.
        bigram_prob (dict): Dictionary containing bigram probabilities.

    Returns:
        float: Trigram probability.

    """
    alpha = 1  # Smoothing parameter
    first_two_words = trigram[:2]

    if first_two_words in bigram_prob and trigram in mle_est:
        first_two_words_count = bigram_prob[first_two_words]
    else:
        first_two_words_count = 0
    # Estimate the vocabulary size based on trigram counts
    vocab_size = donkey
    if trigram in mle_est:
        trigram_count = mle_est[trigram] + alpha
    else:
        trigram_count = alpha
    smoothed_probability = trigram_count / \
        (first_two_words_count + alpha * vocab_size)

    return smoothed_probability


def trigram_perplexity(data, mle_est, bigram_prob, donkey):
    """
    Computes the perplexity for trigram model.

    Args:
        data (list): List of sentences for evaluation.
        mle_est (dict): Dictionary containing trigram counts.
        bigram_prob (dict): Dictionary containing bigram probabilities.

    Returns:
        float: Perplexity score.

    """
    sentence_total, total, sentence_len = 0, 0, 0
    for sentence in data:
        tokens = sentence.split()
        trigrams = [(tokens[i], tokens[i + 1], tokens[i + 2])
                    for i in range(len(tokens) - 2)]
        for trigram in trigrams:
            prob = trigram_mle(trigram, mle_est, bigram_prob, donkey)
            if prob != 0:
                sentence_total += math.log(prob)
        total += sentence_total
        sentence_total = 0
        sentence_len += len(tokens) - 2

    inverse = -1 / sentence_len
    exponent = inverse * total
    perplexity = math.exp(exponent)
    return perplexity


def get_data(words, sentences, file):
    """
    Reads data from the specified file, replaces OOV words with "UNK", and processes sentences.

    Args:
        words (dict): Dictionary of known words.
        sentences (list): List to store processed sentences.
        file (str): File name identifier ("train", "dev", or "test").

    """
    file_map = {
        "dev": "1b_benchmark.dev.tokens",
        "test": "1b_benchmark.test.tokens",
        "train": "1b_benchmark.train.tokens"
    }

    with open(file_map[file], "r", encoding="utf8") as data:
        for sentence in data:
            tokens = sentence.split()
            for i, word in enumerate(tokens):
                if word not in words:
                    tokens[i] = "UNK"
            tokens.insert(0, "<START>")
            tokens.insert(0, "<START>")
            tokens.append("<STOP>")
            sentences.append(" ".join(tokens))


def main():
    """
    Main function to build and evaluate unigram, bigram, and trigram language models.
    """
    unigram, bigram, trigram, prob = {}, {}, {}, {}
    train, dev, test, unk = [], [], [], []

    unigram_data(unigram, unk)
    print("No Smoothing:")
    print("Vocabulary Count: {}".format(len(unigram) - 1))

    get_data(unigram, train, file="train")
    unigram_mle(unigram, prob)
    print("\nUnigram:")
    print("Train Perplexity: {}".format(unigram_perplexity(train, prob)))

    get_data(unigram, dev, file="dev")
    print("Dev Perplexity: {}".format(unigram_perplexity(dev, prob)))

    get_data(unigram, test, file="test")
    print("Test Perplexity: {}\n".format(unigram_perplexity(test, prob)))

    ngram_data(train, 2, bigram)
    # print("Vocabulary Count: {}".format(len(bigram) - 1))
    print("Bigram:")
    print("Train Perplexity: {}".format(
        bigram_perplexity(train, bigram, unigram)))
    print("Dev Perplexity: {}".format(bigram_perplexity(dev, bigram, unigram)))
    print("Test Perplexity: {}\n".format(
        bigram_perplexity(test, bigram, unigram)))

    ngram_data(train, 3, trigram)
    print("Train Perplexity: {}".format(
        trigram_perplexity(train, trigram, bigram, len(unigram) - 1)))
    print("Dev Perplexity: {}".format(
        trigram_perplexity(dev, trigram, bigram, len(unigram) - 1)))
    print("Test Perplexity: {}\n".format(
        trigram_perplexity(test, trigram, bigram, len(unigram) - 1)))


if __name__ == "__main__":
    main()

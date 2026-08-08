def spearman_correlation(xs: list[float], ys: list[float]) -> float:
    def rank(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            average_rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = average_rank
            i = j + 1
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    n = len(xs)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    covariance = sum((a - mean_rx) * (b - mean_ry) for a, b in zip(rx, ry))
    variance_x = sum((a - mean_rx) ** 2 for a in rx)
    variance_y = sum((b - mean_ry) ** 2 for b in ry)
    return covariance / (variance_x * variance_y) ** 0.5

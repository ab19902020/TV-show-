import numpy as np, cv2

def sift_similarity(src, dst, src_mask=None, dst_mask=None, ratio=0.75, reproj=6.0, full_affine=False):
    """Estimate similarity (or affine) transform mapping src image coords -> dst image coords."""
    g1 = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY) if src.ndim == 3 else src
    g2 = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY) if dst.ndim == 3 else dst
    sift = cv2.SIFT_create(nfeatures=6000, contrastThreshold=0.02)
    k1, d1 = sift.detectAndCompute(g1, src_mask)
    k2, d2 = sift.detectAndCompute(g2, dst_mask)
    bf = cv2.BFMatcher(cv2.NORM_L2)
    m = bf.knnMatch(d1, d2, k=2)
    good = [a for a, b in m if a.distance < ratio * b.distance]
    p1 = np.float32([k1[a.queryIdx].pt for a in good])
    p2 = np.float32([k2[a.trainIdx].pt for a in good])
    if full_affine:
        M, inl = cv2.estimateAffine2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=reproj, maxIters=20000, confidence=0.999)
    else:
        M, inl = cv2.estimatePartialAffine2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=reproj, maxIters=20000, confidence=0.999) if hasattr(cv2, "estimatePartialAffine2D") else cv2.estimateAffinePartial2D(p1, p2, method=cv2.RANSAC, ransacReprojThreshold=reproj, maxIters=20000, confidence=0.999)
    n_in = int(inl.sum()) if inl is not None else 0
    return M, n_in, len(good)

def to3(M):
    return np.vstack([M, [0, 0, 1]])

def ecc_refine(src, dst, M, mask=None, iters=200):
    """Refine a 2x3 affine src->dst with ECC (euclidean+scale via affine)."""
    g1 = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    g2 = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    # ECC warps the *input* image into template coords: template=dst, input=src, warp maps template->input
    W = cv2.invertAffineTransform(M).astype(np.float32)
    try:
        _, W = cv2.findTransformECC(g2, g1, W, cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iters, 1e-6), mask, 5)
        return cv2.invertAffineTransform(W)
    except cv2.error:
        return M

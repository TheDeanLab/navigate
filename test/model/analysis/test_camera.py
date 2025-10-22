import numpy as np
import pytest


def test_compute_scmos_offset_and_variance_map():
    from navigate.model.analysis.camera import compute_scmos_offset_and_variance_map

    # deterministic RNG and fixed signal parameters
    rng = np.random.default_rng(0)
    mu, sig = 100.0, 20.0
    frames = 256
    im = sig * rng.standard_normal((256, 256, frames)) + mu

    offset, variance = compute_scmos_offset_and_variance_map(im)

    # theoretical standard errors for per-pixel estimators (normal samples)
    n = frames
    stderr_mean = sig / np.sqrt(n)
    stderr_var = sig * sig * np.sqrt(2.0 / (n - 1))

    # allow a few sigma of the estimator's sampling distribution (e.g. 5\*std)
    atol_mean = 5.0 * stderr_mean
    atol_var = 5.0 * stderr_var

    np.testing.assert_allclose(offset, mu, atol=atol_mean, rtol=0.0)
    np.testing.assert_allclose(variance, sig * sig, atol=atol_var, rtol=0.0)


@pytest.mark.parametrize("local", [True, False])
def test_compute_flatfield_map(local):
    from navigate.model.analysis.camera import compute_flatfield_map

    image = np.ones((256, 256))
    offset = np.zeros((256, 256))
    ffmap = compute_flatfield_map(image, offset, local)

    np.testing.assert_allclose(ffmap, 0.5)


def test_compute_noise_sigma():
    from navigate.model.analysis.camera import compute_noise_sigma

    Fn = np.random.rand()
    qe = np.random.rand()
    S = np.random.rand(256, 256)
    Ib = np.random.rand()
    Nr = np.random.rand()
    M = np.random.rand()
    sigma = compute_noise_sigma(Fn=Fn, qe=qe, S=S, Ib=Ib, Nr=Nr, M=M)
    sigma_true = np.sqrt(Fn * Fn * qe * (S + Ib) + (Nr / M) ** 2)

    np.testing.assert_allclose(sigma, sigma_true)


def test_compute_signal_to_noise():
    from navigate.model.analysis.camera import compute_signal_to_noise

    A = np.random.rand() * 100 + 10
    image = A * np.ones((256, 256))
    offset = np.zeros((256, 256))
    variance = 3 * A * A * np.ones((256, 256))

    snr = compute_signal_to_noise(image, offset, variance)

    np.testing.assert_allclose(snr, 0.5, rtol=0.2)

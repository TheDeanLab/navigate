import numpy as np
import pytest


@pytest.mark.skip("volatile")
def test_compute_scmos_offset_and_variance_map():
    from navigate.model.analysis.camera import compute_scmos_offset_and_variance_map

    mu, sig = 100 * np.random.rand() + 1, 100 * np.random.rand() + 1
    im = sig * np.random.randn(256, 256, 256) + mu

    offset, variance = compute_scmos_offset_and_variance_map(im)

    print(mu, sig)
    # TODO: 1 is a bit high?
    np.testing.assert_allclose(offset, mu, rtol=1)
    np.testing.assert_allclose(variance, sig * sig, rtol=1)


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

import numpy as np
from BOF import BagOfFeaturesEncoder
from BOF.imageencoding import collect_normalised_patches, Augment, _combine_proj_whiten

class testPatchExtractor():
    def setUp(self):
        self.images = (np.random.randint(0, high=255, size=(50,50)) for i in range(10))

    def test_collection(self):
        patches = collect_normalised_patches(self.images, 10)
        assert patches.shape == (1000, 49)
        mag = np.linalg.norm(patches, axis=1)
        assert np.logical_and(mag > 0, mag <= 1).all()


class testBOF():
    def setUp(self):
        """Generate series of random images for sampling."""
        self.images = (np.random.randint(0, high=255, size=(50,50)) for i in range(10))
        self.bof = BagOfFeaturesEncoder(n_patches=100)
        self.bof.fit(self.images, 10)
        self.hier = BagOfFeaturesEncoder(n_patches=10, levels=2)
        self.hier.fit(self.images, 10)
        self.augment = BagOfFeaturesEncoder(n_patches=10, levels=2, augment='rotate')
        self.augment.fit(self.images, 10)
        self.test_images = [np.random.rand(50, 50) for i in range(2)]

    def test_centroids(self):
        assert self.bof.cluster.centroids.shape == (10, 49)
        assert np.isfinite(self.bof.cluster.centroids).all()

    def test_transform_reshape(self):
        output = self.bof.transform(self.test_images[0], reshape=True)
        assert output.shape == (44, 44, 10) # Patches are lost at the boundaries
        assert output.dtype =='bool'

    def test_transform_noreshape(self):
        output = self.bof.transform(self.test_images[0], reshape=False)
        assert output.shape == (44*44, ) # Patches are lost at the boundaries

    def test_predict(self):
        output = self.bof.predict(self.test_images)
        assert output.shape == (2, 10)
        assert (output.sum(axis=1) == 44*44).all()

    def test_hier_predict(self):
        output = self.hier.predict(self.test_images)
        assert output.shape == (2, 100)
        assert (output.sum(axis=1) == 44*44).all()

    def test_hier_transform(self):
        output = self.hier.transform(self.test_images[0])
        assert output.shape == (44*44,)
        assert np.logical_and(output < 100, output >= 0).all()

    def test_predict_pixels(self):
        prediction = self.bof.predict_pixels(self.test_images[0])
        assert prediction.shape == (44, 44, 10)
        assert (prediction.sum(axis=2) == 1).all()

    def test_augment(self):
        histograms = self.augment.predict(self.test_images)
        histograms_pooled = self.augment.predict(self.test_images, pool=True)
        assert histograms.shape == (8, 100)
        assert histograms_pooled.shape == (2,100)
        assert histograms.sum() == histograms_pooled.sum()


class testAugment():
    def setUp(self):
        self.image = np.random.rand(40,30)
    
    def test_rotate(self):
        augment = Augment('rotate')
        augmented = augment(self.image)
        assert len(augmented) == 4
        assert augmented[0].shape == augmented[2].shape == (40, 30)
        assert augmented[1].shape == augmented[3].shape == (30, 40)
        assert (np.rot90(augmented[-1]) == self.image).all

    def test_reflect(self):
        augment = Augment('reflect')
        augmented = augment(self.image)
        assert len(augmented) == 3
        assert augmented[0].shape == augmented[1].shape == augmented[2].shape == (40, 30)
        assert (np.flipud(augmented[2]) == self.image).all()
        assert (np.fliplr(augmented[1]) == self.image).all()

    def test_both(self):
        augment = Augment('both')
        augmented = augment(self.image)
        assert len(augmented) == 12


def test_combine():
    images = (np.random.randint(0, high=255, size=(50,50)) for i in range(10))
    bof = BagOfFeaturesEncoder(levels=2)
    bof.fit(images, 10)
    whiten = bof.whiten.whiten
    centroids = bof.cluster.centroids
    new_centroids = _combine_proj_whiten(centroids, whiten, 2)
    assert len(new_centroids) == 11
    top = np.dot(whiten, centroids[0].T).T
    end = np.dot(whiten, centroids[-1][-1].T).T
    assert np.allclose(top, new_centroids[0])
    assert np.allclose(end, new_centroids[-1][-1])


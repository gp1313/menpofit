from __future__ import division
from functools import partial
import numpy as np

from menpo.shape import PointCloud
from menpo.transform import (scale_about_centre, rotate_ccw_about_centre,
                             Translation, Scale, AlignmentAffine,
                             AlignmentSimilarity)

import menpofit.checks as checks
from menpofit.visualize import print_progress


def noisy_alignment_similarity_transform(source, target, noise_type='uniform',
                                         noise_percentage=0.1, rotation=False):
    r"""
    Constructs and perturbs the optimal similarity transform between the source
    and target shapes by adding noise to its parameters.

    Parameters
    ----------
    source : `menpo.shape.PointCloud`
        The source pointcloud instance used in the alignment
    target : `menpo.shape.PointCloud`
        The target pointcloud instance used in the alignment
    noise_type : ``{'uniform', 'gaussian'}``, optional
        The type of noise to be added.
    noise_percentage : `float` in ``(0, 1)`` or `list` of `len` `3`, optional
        The standard percentage of noise to be added. If `float`, then the same
        amount of noise is applied to the scale, rotation and translation
        parameters of the optimal similarity transform. If `list` of
        `float` it must have length 3, where the first, second and third elements
        denote the amount of noise to be applied to the scale, rotation and
        translation parameters, respectively.
    rotation : `bool`, optional
        If ``False``, then the rotation is not considered when computing the
        optimal similarity transform between source and target.

    Returns
    -------
    noisy_alignment_similarity_transform : `menpo.transform.Similarity`
        The noisy Similarity Transform between source and target.
    """
    if isinstance(noise_percentage, float):
        noise_percentage = [noise_percentage] * 3
    elif len(noise_percentage) == 1:
        noise_percentage *= 3

    similarity = AlignmentSimilarity(source, target, rotation=rotation)

    if noise_type is 'gaussian':
        s = noise_percentage[0] * (0.5 / 3) * np.asscalar(np.random.randn(1))
        r = noise_percentage[1] * (180 / 3) * np.asscalar(np.random.randn(1))
        t = noise_percentage[2] * (target.range() / 3) * np.random.randn(2)

        s = scale_about_centre(target, 1 + s)
        r = rotate_ccw_about_centre(target, r)
        t = Translation(t, source.n_dims)
    elif noise_type is 'uniform':
        s = noise_percentage[0] * 0.5 * (2 * np.asscalar(np.random.randn(1)) - 1)
        r = noise_percentage[1] * 180 * (2 * np.asscalar(np.random.rand(1)) - 1)
        t = noise_percentage[2] * target.range() * (2 * np.random.rand(2) - 1)

        s = scale_about_centre(target, 1. + s)
        r = rotate_ccw_about_centre(target, r)
        t = Translation(t, source.n_dims)
    else:
        raise ValueError('Unexpected noise type. '
                         'Supported values are {gaussian, uniform}')

    return similarity.compose_after(t.compose_after(s.compose_after(r)))


def noisy_target_alignment_transform(source, target,
                                     alignment_transform_cls=AlignmentAffine,
                                     noise_std=0.1, **kwargs):
    r"""
    Constructs the optimal alignment transform between the source and a noisy
    version of the target obtained by adding white noise to each of its points.

    Parameters
    ----------
    source : `menpo.shape.PointCloud`
        The source pointcloud instance used in the alignment
    target : `menpo.shape.PointCloud`
        The target pointcloud instance used in the alignment
    alignment_transform_cls : `menpo.transform.Alignment`, optional
        The alignment transform class used to perform the alignment.
    noise_std : `float` or `list` of `float`, optional
        The standard deviation of the white noise to be added to each one of
        the target points. If `float`, then the same standard deviation is used
        for all points. If `list`, then it must define a value per point.

    Returns
    -------
    noisy_transform : `menpo.transform.Alignment`
        The noisy Similarity Transform
    """
    noise = noise_std * target.range() * np.random.randn(target.n_points,
                                                         target.n_dims)
    noisy_target = PointCloud(target.points + noise)
    return alignment_transform_cls(source, noisy_target, **kwargs)


def noisy_shape_from_bounding_box(shape, bounding_box, noise_type='uniform',
                                  noise_percentage=0.05, rotation=False):
    r"""
    Constructs and perturbs the optimal similarity transform between the bounding
    box of the source shape and the target bounding box, by adding noise to its
    parameters. It returns the noisy version of the provided shape.

    Parameters
    ----------
    shape : `menpo.shape.PointCloud`
        The source pointcloud instance used in the alignment. Note that the
        bounding box of the shape will be used.
    bounding_box : `menpo.shape.PointDirectedGraph`
        The target bounding box instance used in the alignment
    noise_type : ``{'uniform', 'gaussian'}``, optional
        The type of noise to be added.
    noise_percentage : `float` in ``(0, 1)`` or `list` of `len` `3`, optional
        The standard percentage of noise to be added. If `float`, then the same
        amount of noise is applied to the scale, rotation and translation
        parameters of the optimal similarity transform. If `list` of
        `float` it must have length 3, where the first, second and third elements
        denote the amount of noise to be applied to the scale, rotation and
        translation parameters, respectively.
    rotation : `bool`, optional
        If ``False``, then the rotation is not considered when computing the
        optimal similarity transform between source and target.

    Returns
    -------
    noisy_shape : `menpo.shape.PointCloud`
        The noisy shape.
    """
    transform = noisy_alignment_similarity_transform(
        shape.bounding_box(), bounding_box, noise_type=noise_type,
        noise_percentage=noise_percentage, rotation=rotation)
    return transform.apply(shape)


def noisy_shape_from_shape(reference_shape, shape, noise_type='uniform',
                           noise_percentage=0.05, rotation=False):
    r"""
    Constructs and perturbs the optimal similarity transform between the provided
    reference shape and the target shape, by adding noise to its parameters. It
    returns the noisy version of the reference shape.

    Parameters
    ----------
    reference_shape : `menpo.shape.PointCloud`
        The source reference shape instance used in the alignment.
    shape : `menpo.shape.PointDirectedGraph`
        The target shape instance used in the alignment
    noise_type : ``{'uniform', 'gaussian'}``, optional
        The type of noise to be added.
    noise_percentage : `float` in ``(0, 1)`` or `list` of `len` `3`, optional
        The standard percentage of noise to be added. If `float`, then the same
        amount of noise is applied to the scale, rotation and translation
        parameters of the optimal similarity transform. If `list` of
        `float` it must have length 3, where the first, second and third elements
        denote the amount of noise to be applied to the scale, rotation and
        translation parameters, respectively.
    rotation : `bool`, optional
        If ``False``, then the rotation is not considered when computing the
        optimal similarity transform between source and target.

    Returns
    -------
    noisy_reference_shape : `menpo.shape.PointCloud`
        The noisy reference shape.
    """
    transform = noisy_alignment_similarity_transform(
        reference_shape, shape, noise_type=noise_type,
        noise_percentage=noise_percentage, rotation=rotation)
    return transform.apply(reference_shape)


def align_shape_with_bounding_box(shape, bounding_box,
                                  alignment_transform_cls=AlignmentSimilarity,
                                  **kwargs):
    r"""
    Aligns the provided shape with the bounding box using a particular alignment
    transform.

    Parameters
    ----------
    shape : `menpo.shape.PointCloud`
        The shape instance used in the alignment.
    bounding_box : `menpo.shape.PointDirectedGraph`
        The bounding box instance used in the alignment.
    alignment_transform_cls : `menpo.transform.Alignment`, optional
        The class of the alignment transform used to perform the alignment.

    Returns
    -------
    noisy_shape : `menpo.shape.PointCloud`
        The noisy shape
    """
    shape_bb = shape.bounding_box()
    transform = alignment_transform_cls(shape_bb, bounding_box, **kwargs)
    return transform.apply(shape)


class MultiFitter(object):
    r"""
    Abstract class for a multi-scale fitter.
    """
    @property
    def n_scales(self):
        r"""
        Returns the number of scales used during fitting.

        :type: `int`
        """
        return len(self.scales)

    def fit_from_shape(self, image, initial_shape, max_iters=20, gt_shape=None,
                       crop_image=None, **kwargs):
        r"""
        Fits the multi-scale fitter to an image given an initial shape.

        Parameters
        ----------
        image : `menpo.image.Image` or subclass
            The image to be fitted.
        initial_shape : `menpo.shape.PointCloud`
            The initial shape estimate from which the fitting procedure
            will start.
        max_iters : `int` or `list` of `int`, optional
            The maximum number of iterations. If `int`, then it specifies the
            maximum number of iterations over all scales. If `list` of `int`,
            then specifies the maximum number of iterations per scale.
        gt_shape : `menpo.shape.PointCloud`, optional
            The ground truth shape associated to the image.
        crop_image : ``None`` or `float`, optional
            If `float`, it specifies the proportion of the border wrt the
            initial shape to which the image will be internally cropped around
            the initial shape range. If ``None``, no cropping is performed.
            This will limit the fitting algorithm search region but is
            likely to speed up its running time, specially when the
            modeled object occupies a small portion of the image.
        kwargs : `dict`, optional
            Additional keyword arguments that can be passed to specific
            implementations.

        Returns
        -------
        fitting_result : `class` (see below)
            The multi-scale fitting result containing the result of the fitting
            procedure. It can be a :map:`MultiScaleNonParametricIterativeResult`
            or :map:`MultiScaleParametricIterativeResult` or `subclass` of those.
        """
        # generate the list of images to be fitted
        images, initial_shapes, gt_shapes = self._prepare_image(
            image, initial_shape, gt_shape=gt_shape, crop_image=crop_image)

        # work out the affine transform between the initial shape of the
        # highest pyramidal level and the initial shape of the original image
        affine_correction = AlignmentAffine(initial_shapes[-1], initial_shape)

        # run multilevel fitting
        algorithm_results = self._fit(images, initial_shapes[0],
                                      max_iters=max_iters,
                                      gt_shapes=gt_shapes, **kwargs)

        # build multilevel fitting result
        fitter_result = self._fitter_result(
            image, algorithm_results, affine_correction, gt_shape=gt_shape)

        return fitter_result

    def fit_from_bb(self, image, bounding_box, max_iters=20, gt_shape=None,
                    crop_image=None, **kwargs):
        r"""
        Fits the multi-scale fitter to an image given an initial bounding box.

        Parameters
        ----------
        image : `menpo.image.Image` or subclass
            The image to be fitted.
        bounding_box : `menpo.shape.PointDirectedGraph`
            The initial bounding box from which the fitting procedure will
            start. Note that the bounding box is used in order to align the
            model's reference shape.
        max_iters : `int` or `list` of `int`, optional
            The maximum number of iterations. If `int`, then it specifies the
            maximum number of iterations over all scales. If `list` of `int`,
            then specifies the maximum number of iterations per scale.
        gt_shape : `menpo.shape.PointCloud`, optional
            The ground truth shape associated to the image.
        crop_image : ``None`` or `float`, optional
            If `float`, it specifies the proportion of the border wrt the
            initial shape to which the image will be internally cropped around
            the initial shape range. If ``None`` , no cropping is performed.
            This will limit the fitting algorithm search region but is
            likely to speed up its running time, specially when the
            modeled object occupies a small portion of the image.
        kwargs : `dict`, optional
            Additional keyword arguments that can be passed to specific
            implementations.

        Returns
        -------
        fitting_result : `class` (see below)
            The multi-scale fitting result containing the result of the fitting
            procedure. It can be a :map:`MultiScaleNonParametricIterativeResult`
            or :map:`MultiScaleParametricIterativeResult` or `subclass` of those.
        """
        initial_shape = align_shape_with_bounding_box(self.reference_shape,
                                                      bounding_box)
        return self.fit_from_shape(image, initial_shape, max_iters=max_iters,
                                   gt_shape=gt_shape, crop_image=crop_image,
                                   **kwargs)

    def _prepare_image(self, image, initial_shape, gt_shape=None,
                       crop_image=0.5):
        # Attach landmarks to the image
        image.landmarks['__initial_shape'] = initial_shape
        if gt_shape:
            image.landmarks['__gt_shape'] = gt_shape

        tmp_image = image
        if crop_image:
            # If specified, crop the image
            tmp_image = image.crop_to_landmarks_proportion(
                    crop_image, group='__initial_shape')

        # Rescale image wrt the scale factor between reference_shape and
        # initial_shape
        tmp_image = tmp_image.rescale_to_pointcloud(
                self.reference_shape, group='__initial_shape')

        # Compute image representation
        images = []
        for i in range(self.n_scales):
            # Handle features
            if i == 0 or self.holistic_features[i] is not self.holistic_features[i - 1]:
                # Compute features only if this is the first pass through
                # the loop or the features at this scale are different from
                # the features at the previous scale
                feature_image = self.holistic_features[i](tmp_image)

            # Handle scales
            if self.scales[i] != 1:
                # Scale feature images only if scale is different than 1
                scaled_image = feature_image.rescale(self.scales[i])
            else:
                scaled_image = feature_image

            # Add scaled image to list
            images.append(scaled_image)

        # Get initial shapes per level
        initial_shapes = [i.landmarks['__initial_shape'].lms for i in images]

        # Get ground truth shapes per level
        if gt_shape:
            gt_shapes = [i.landmarks['__gt_shape'].lms for i in images]
        else:
            gt_shapes = None

        # detach added landmarks from image
        del image.landmarks['__initial_shape']
        if gt_shape:
            del image.landmarks['__gt_shape']

        return images, initial_shapes, gt_shapes

    def _fit(self, images, initial_shape, gt_shapes=None, max_iters=20,
             **kwargs):
        # Perform check
        max_iters = checks.check_max_iters(max_iters, self.n_scales)

        # Set initial and ground truth shapes
        shape = initial_shape
        gt_shape = None

        # Initialize list of algorithm results
        algorithm_results = []
        for i in range(self.n_scales):
            # Handle ground truth shape
            if gt_shapes is not None:
                gt_shape = gt_shapes[i]

            # Run algorithm
            algorithm_result = self.algorithms[i].run(images[i], shape,
                                                      gt_shape=gt_shape,
                                                      max_iters=max_iters[i],
                                                      **kwargs)
            # Add algorithm result to the list
            algorithm_results.append(algorithm_result)

            # Prepare this scale's final shape for the next scale
            shape = algorithm_result.final_shape
            if self.scales[i] != self.scales[-1]:
                shape = Scale(self.scales[i + 1] / self.scales[i],
                              n_dims=shape.n_dims).apply(shape)

        # Return list of algorithm results
        return algorithm_results


class ModelFitter(MultiFitter):
    r"""
    Abstract class for fitting a multi-scale model.
    """
    @property
    def reference_shape(self):
        r"""
        The reference shape of the model.

        :type: `menpo.shape.PointCloud`
        """
        return self._model.reference_shape

    @property
    def holistic_features(self):
        r"""
        The holistic features utilized by the model.

        :type: `list` of `callable`
        """
        return self._model.holistic_features

    @property
    def scales(self):
        r"""
        The `list` of scale values of the model.

        :type: `list`
        """
        return self._model.scales

    def perturb_from_bb(self, gt_shape, bb,
                        perturb_func=noisy_shape_from_bounding_box):
        """
        Returns a perturbed version of the ground truth shape. The perturbation
        is applied on the alignment between the ground truth bounding box and
        the provided bounding box. This is useful for obtaining the initial
        bounding box of the fitting.

        Parameters
        ----------
        gt_shape : `menpo.shape.PointCloud`
            The ground truth shape.
        bb : `menpo.shape.PointDirectedGraph`
            The target bounding box.
        perturb_func : `callable`, optional
            The function that will be used for generating the perturbations.

        Returns
        -------
        perturbed_shape : `menpo.shape.PointCloud`
            The perturbed shape.
        """
        return perturb_func(gt_shape, bb)

    def perturb_from_gt_bb(self, gt_bb,
                           perturb_func=noisy_shape_from_bounding_box):
        """
        Returns a perturbed version of the ground truth bounding box. This is
        useful for obtaining the initial bounding box of the fitting.

        Parameters
        ----------
        gt_bb : `menpo.shape.PointDirectedGraph`
            The ground truth bounding box.
        perturb_func : `callable`, optional
            The function that will be used for generating the perturbations.

        Returns
        -------
        perturbed_bb : `menpo.shape.PointDirectedGraph`
            The perturbed ground truth bounding box.
        """
        return perturb_func(gt_bb, gt_bb)


def generate_perturbations_from_gt(images, n_perturbations, perturb_func,
                                   gt_group=None, bb_group_glob=None,
                                   verbose=False):
    """
    Function that returns a callable that generates perturbations of the bounding
    boxes of the provided images.

    Parameters
    ----------
    images : `list` of `menpo.image.Image`
        The list of images.
    n_perturbations : `int`
        The number of perturbed shapes to be generated per image.
    perturb_func : `callable`
        The function that will be used for generating the perturbations.
    gt_group : `str`
        The group of the ground truth shapes attached to the images.
    bb_group_glob : `str`
        The group of the bounding boxes attached to the images.
    verbose : `bool`, optional
        If ``True``, then progress information is printed.

    Returns
    -------
    generated_bb_func : `callable`
        The function that generates the perturbations.
    """
    if bb_group_glob is None:
        bb_generator = lambda im: [im.landmarks[gt_group].lms.bounding_box()]
        n_bbs = 1
    else:
        def bb_glob(im):
            for k, v in im.landmarks.items_matching(bb_group_glob):
                yield v.lms.bounding_box()
        bb_generator = bb_glob
        n_bbs = len(list(bb_glob(images[0])))

    if n_bbs == 0:
        raise ValueError('Must provide a valid bounding box glob - no bounding '
                         'boxes matched the following '
                         'glob: {}'.format(bb_group_glob))

    # If we have multiple boxes - we didn't just throw them away, we re-add them
    # to the end
    if bb_group_glob is not None:
        msg = '- Generating {0} ({1} perturbations * {2} provided boxes) new ' \
              'initial bounding boxes + {2} provided boxes per image'.format(
            n_perturbations * n_bbs, n_perturbations, n_bbs)
    else:
        msg = '- Generating {} new bounding boxes directly from the ' \
              'ground truth shape'.format(n_perturbations)

    wrap = partial(print_progress, prefix=msg, verbose=verbose)
    for im in wrap(images):
        gt_s = im.landmarks[gt_group].lms.bounding_box()

        k = 0
        for bb in bb_generator(im):
            for _ in range(n_perturbations):
                p_s = perturb_func(gt_s, bb).bounding_box()
                perturb_bbox_group = '__generated_bb_{}'.format(k)
                im.landmarks[perturb_bbox_group] = p_s
                k += 1

            if bb_group_glob is not None:
                perturb_bbox_group = '__generated_bb_{}'.format(k)
                im.landmarks[perturb_bbox_group] = bb
                k += 1

        if im.has_landmarks_outside_bounds:
            im.constrain_landmarks_to_bounds()

    generated_bb_func = lambda x: [v.lms for k, v in x.landmarks.items_matching(
        '__generated_bb_*')]
    return generated_bb_func

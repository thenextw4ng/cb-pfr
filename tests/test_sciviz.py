"""Lightweight tests for evidence-aware scientific visualization helpers."""
import unittest

import numpy as np

from cbpfr.sciviz import (
    axis_centers,
    distribution_figure,
    field_figure,
    profile_figure,
    uncertainty_figure,
    vtk_plane_html,
)


class ScientificVisualizationTests(unittest.TestCase):
    def test_axis_centers_use_mesh_bounds_only_when_valid(self):
        centers, label = axis_centers((0.0, 3.0), 3)
        np.testing.assert_allclose(centers, [0.5, 1.5, 2.5])
        self.assertEqual(label, "Position (cm)")

        indices, index_label = axis_centers(None, 3)
        np.testing.assert_allclose(indices, [0.0, 1.0, 2.0])
        self.assertEqual(index_label, "Mesh-bin index")

        indices_bad, bad_label = axis_centers((4.0, 1.0), 3)
        np.testing.assert_allclose(indices_bad, [0.0, 1.0, 2.0])
        self.assertEqual(bad_label, "Mesh-bin index")

    def test_field_figure_links_selected_row_and_adds_contours(self):
        x = np.arange(4, dtype=float)
        y = np.arange(3, dtype=float)
        mean = np.array(
            [[1e-3, 2e-3, 4e-3, 8e-3],
             [2e-3, 4e-3, 8e-3, 1.6e-2],
             [4e-3, 8e-3, 1.6e-2, 3.2e-2]],
            dtype=float,
        )
        fig = field_figure(mean, x, y, "flux", selected_row=1)
        self.assertEqual(len(fig.data), 3)
        self.assertEqual(fig.data[0].type, "heatmap")
        self.assertEqual(fig.data[1].type, "contour")
        self.assertEqual(fig.data[2].type, "scatter")
        np.testing.assert_allclose(fig.data[2].y, [1.0, 1.0])
        self.assertIn("contour", fig.layout.title.text.lower())

    def test_field_figure_keeps_linear_values_for_hover(self):
        values = np.array([[0.0, 1.0], [2.0, 4.0]])
        fig = field_figure(
            values,
            np.array([0.0, 1.0]),
            np.array([0.0, 1.0]),
            "fission",
            selected_row=0,
            log_color=True,
        )
        np.testing.assert_allclose(fig.data[0].customdata, values)
        self.assertTrue(np.isnan(np.asarray(fig.data[0].z, dtype=float)[0, 0]))

    def test_profile_displays_reported_tally_sd(self):
        x = np.array([0.0, 1.0, 2.0])
        mean = np.array([1.2, 1.4, 1.5])
        sd = np.array([0.01, 0.02, 0.03])
        fig = profile_figure(x, mean, sd, "flux", row_index=4, x_label="x-bin")
        np.testing.assert_allclose(fig.data[0].y, mean)
        np.testing.assert_allclose(fig.data[0].error_y.array, sd)
        self.assertIn("row 4", fig.layout.title.text.lower())

    def test_vtk_trame_export_returns_embeddable_html_scene(self):
        values = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float)
        html = vtk_plane_html(
            values,
            x_bounds=(0.0, 2.0),
            y_bounds=(0.0, 2.0),
            score_name="flux",
        )
        self.assertIn("<html", html.lower())
        self.assertIn("offlinelocalview.load", html.lower())
        self.assertIn("</html>", html.lower())

    def test_uncertainty_and_distribution_figures_accept_spatial_arrays(self):
        x = np.array([0.0, 1.0])
        y = np.array([0.0, 1.0])
        rel = np.array([[0.1, np.nan], [0.2, 0.4]])
        unc = uncertainty_figure(rel, x, y, "nu-fission")
        self.assertEqual(unc.data[0].type, "heatmap")
        self.assertEqual(unc.data[0].z.shape, (2, 2))

        dist = distribution_figure(np.array([0.0, 0.2, 0.4, np.nan]), "fission")
        self.assertEqual(dist.data[0].type, "histogram")
        self.assertEqual(len(dist.data[0].x), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)

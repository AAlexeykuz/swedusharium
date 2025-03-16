import numpy as np
import matplotlib.pyplot as plt
from cogwheels.neurosphere import Neurosphere
import logging


def plot_sphere_points(points, colors):
    """
    Visualize points on a 3D sphere with custom colors.
    Only displays points that are visible from the current camera position.
    The visible points are recalculated whenever the view is updated.

    Args:
        points (numpy.ndarray): Array of shape (n, 2) containing (latitude, longitude) in radians.
        colors (dict): Dictionary mapping (latitude, longitude) tuples to RGB color tuples.
    """
    # Convert lat/lon to Cartesian coordinates on the unit sphere.
    # (latitude, longitude) where latitude is in [-pi/2, pi/2] and longitude in [-pi, pi].
    x = np.cos(points[:, 0]) * np.cos(points[:, 1])
    y = np.cos(points[:, 0]) * np.sin(points[:, 1])
    z = np.sin(points[:, 0])
    points_cartesian = np.stack([x, y, z], axis=1)

    # Create the figure and 3D axis.
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Initial calculation of the visible mask based on current view.
    def get_camera_direction():
        """
        Compute the camera viewing direction vector from the axes’ current azimuth and elevation.
        Matplotlib defines:
          - azimuth (azim): rotation about the z-axis (in degrees)
          - elevation (elev): angle above the xy-plane (in degrees)
        The conversion below gives a unit vector.
        """
        azim = np.deg2rad(ax.azim)
        elev = np.deg2rad(ax.elev)
        # Note: This conversion assumes the camera is at a large distance so that the view
        # is roughly along the vector defined by azim and elev.
        camera_dir = np.array([
            np.cos(elev) * np.cos(azim),
            np.cos(elev) * np.sin(azim),
            np.sin(elev)
        ])
        return camera_dir

    visible_border = 0

    def update_visible_points(event=None):
        # Get the current camera direction from the axis.
        camera_dir = get_camera_direction()
        # For each sphere point (which is also a unit vector), compute its dot product with camera_dir.
        # If the dot is positive, the point is facing the camera.
        dots = np.dot(points_cartesian, camera_dir)
        visible_mask = dots > visible_border

        # Filter visible points.
        x_vis = x[visible_mask]
        y_vis = y[visible_mask]
        z_vis = z[visible_mask]

        # Update scatter data.
        scatter._offsets3d = (x_vis, y_vis, z_vis)

        # Update colors for visible points.
        points_vis = points[visible_mask]
        new_color_list = []
        for point in points_vis:
            lat = float(point[0])
            lon = float(point[1])
            rgb = colors[(lat, lon)]
            normalized_rgb = [c / 255.0 for c in rgb]
            new_color_list.append(normalized_rgb)
        new_color_array = np.array(new_color_list)
        scatter.set_facecolor(new_color_array)

        # Update the title with the current count of visible points.
        ax.set_title(f'Visible Neurosphere Points ({len(x_vis)} Points)', fontsize=14)
        fig.canvas.draw_idle()

    # Initially compute visible points.
    camera_dir = get_camera_direction()
    dots = np.dot(points_cartesian, camera_dir)
    visible_mask = dots > visible_border
    x_vis = x[visible_mask]
    y_vis = y[visible_mask]
    z_vis = z[visible_mask]

    # Build color array for the initially visible points.
    color_list = []
    points_vis = points[visible_mask]
    for point in points_vis:
        lat = float(point[0])
        lon = float(point[1])
        rgb = colors[(lat, lon)]
        normalized_rgb = [c / 255.0 for c in rgb]
        color_list.append(normalized_rgb)
    color_array = np.array(color_list)

    # Plot the visible points.
    scatter = ax.scatter(x_vis, y_vis, z_vis, s=100, c=color_array, alpha=1)

    # Draw a wireframe sphere for context.
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    sphere_x = np.outer(np.cos(u), np.sin(v))
    sphere_y = np.outer(np.sin(u), np.sin(v))
    sphere_z = np.outer(np.ones(np.size(u)), np.cos(v))
    ax.plot_wireframe(sphere_x, sphere_y, sphere_z, color='gray', alpha=0)

    # Configure the axis appearance.
    ax.set_box_aspect([1, 1, 1])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    # Connect an event handler to update visible points after a view change.
    # You might use 'button_release_event' (after rotating with the mouse) and 'key_release_event' (for keyboard changes).
    fig.canvas.mpl_connect('button_release_event', update_visible_points)
    fig.canvas.mpl_connect('key_release_event', update_visible_points)

    plt.tight_layout()
    return fig, ax


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Приложение запущено")

    sphere = Neurosphere()
    points = sphere.points

    # tectonics, tectonics_number = sphere.generate_tectonics()
    # noise_map = sphere.generate_heights(tectonics, tectonics_number)
    # colors = sphere.generate_colors_by_height_map(noise_map)

    # tectonics, tectonic_colors, _ = sphere.generate_tectonics()
    # colors = sphere.generate_colors_by_tectonic(tectonics, tectonic_colors)
    # fig, ax = plot_sphere_points(points, colors)
    # plt.show()

    heat_map = sphere.generate_heat_map()
    colors = sphere.generate_colors_by_map(heat_map)

    fig, ax = plot_sphere_points(points, colors)
    plt.show()


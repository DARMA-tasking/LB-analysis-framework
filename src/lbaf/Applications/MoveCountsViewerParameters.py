class MoveCountsViewerParameters:
    """ A class to describe MoveCountsViewer parameters
    """

    def __init__(self, viewer):

        # Set parameters based on viewer's attribute values

        # Set renderer parameters
        self.renderer_background = [1, 1, 1]

        # Set actor_vertices parameters
        self.actor_vertices_screen_size = 50 if viewer.interactive else 5000
        self.actor_vertices_color = [0, 0, 0]
        self.actor_vertices_opacity = .3 if viewer.interactive else .5

        # Set actor_labels parameters
        self.actor_labels_color = [0, 0, 0]
        self.actor_labels_font_size = 16 if viewer.interactive else 150
        self.actor_edges_opacity = .5 if viewer.interactive else 1
        self.actor_edges_line_width = 2 if viewer.interactive else 15

        # Set actor_arrows parameters
        self.actor_arrows_edge_glyph_position = .5
        self.actor_arrows_source_scale = .075

        # Set actor_bar parameters
        self.actor_bar_number_of_labels = 2
        self.actor_bar_width = .2
        self.actor_bar_heigth = .08
        self.actor_bar_position = [.4, .91]
        self.actor_bar_title_color = [0, 0, 0]
        self.actor_bar_label_color = [0, 0, 0]

        # Set window parameters
        self.window_size_x = 600
        self.window_size_y = 600

        # Set wti (WindowToImageFilter) parameters
        self.wti_scale = 10

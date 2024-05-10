import functools

import ipywidgets as widgets


# This will make a little control panel to help us align things
def make_control_panel(m):
    def create_expanded_button(description):
        return widgets.Button(
            description=description,
            button_style="warning",
            layout=widgets.Layout(height="auto", width="auto"),
        )

    def button_move(b, dx=0, dy=0):
        m.move(dx=dx, dy=dy)

    control_panel = widgets.GridspecLayout(7, 7)

    # y buttons
    bp5y = create_expanded_button("+5mm")
    bp5y.on_click(functools.partial(button_move, dx=0, dy=5))
    control_panel[0, 3] = bp5y

    bp1y = create_expanded_button("+1mm")
    bp1y.on_click(functools.partial(button_move, dx=0, dy=1))
    control_panel[1, 3] = bp1y

    bppt1y = create_expanded_button("+.1mm")
    bppt1y.on_click(functools.partial(button_move, dx=0, dy=0.1))
    control_panel[2, 3] = bppt1y

    bmpt1y = create_expanded_button("-.1mm")
    bmpt1y.on_click(functools.partial(button_move, dx=0, dy=-0.1))
    control_panel[4, 3] = bmpt1y

    bm1y = create_expanded_button("-1mm")
    bm1y.on_click(functools.partial(button_move, dx=0, dy=-1))
    control_panel[5, 3] = bm1y

    bm5y = create_expanded_button("-5mm")
    bm5y.on_click(functools.partial(button_move, dx=0, dy=-5))
    control_panel[6, 3] = bm5y

    # x buttons
    bp5x = create_expanded_button("+5mm")
    bp5x.on_click(functools.partial(button_move, dx=5, dy=0))
    control_panel[3, 6] = bp5x

    bp1x = create_expanded_button("+1mm")
    bp1x.on_click(functools.partial(button_move, dx=1, dy=0))
    control_panel[3, 5] = bp1x

    bppt1x = create_expanded_button("+.1mm")
    bppt1x.on_click(functools.partial(button_move, dx=0.1, dy=0))
    control_panel[3, 4] = bppt1x

    bmpt1x = create_expanded_button("-.1mm")
    bmpt1x.on_click(functools.partial(button_move, dx=-0.1, dy=0))
    control_panel[3, 2] = bmpt1x

    bm1x = create_expanded_button("-1mm")
    bm1x.on_click(functools.partial(button_move, dx=-1, dy=0))
    control_panel[3, 1] = bm1x

    bm5x = create_expanded_button("-5mm")
    bm5x.on_click(functools.partial(button_move, dx=-5, dy=0))
    control_panel[3, 0] = bm5x

    return control_panel

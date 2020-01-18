# rv3d
def get_hovered_region_3d(context, mouse_position):
    mouse_x, mouse_y = mouse_position
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            header = next(r for r in area.regions if r.type == 'HEADER')
            tools = next(r for r in area.regions if r.type == 'TOOLS')  # N-panel
            ui = next(r for r in area.regions if r.type == 'UI')  # T-panel

            min_x = area.x + tools.width
            max_x = area.x + area.width - ui.width
            min_y = area.y
            max_y = area.y + area.height

            if header.alignment == 'TOP':
                max_y -= header.height
            elif header.alignment == 'BOTTOM':
                min_y += header.height

            if min_x <= mouse_x < max_x and min_y <= mouse_y < max_y:
                if len(area.spaces.active.region_quadviews) == 0:
                    return area.spaces.active.region_3d
                else:
                    # Not sure quadview support required?
                    pass

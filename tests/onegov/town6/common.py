
def step_class(page, step):
    return page.pyquery(f'[data-step="{step}"]').attr('class')

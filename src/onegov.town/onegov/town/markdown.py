""" Customizations of the markdown renderer. """

import mistune


class RelativeHeaderRenderer(mistune.Renderer):

    def header(self, text, level, raw=None):
        """ Renders the headers starting at level 2. That is, there's no
        <h1> and the "# title" results in <h2>title</h2>.

        The reason for this is the fact that the page titles are h1
        and we want to subjugate all other headers under it.

        """
        if level <= 5:
            level += 1

        return super(RelativeHeaderRenderer, self).header(text, level, raw)

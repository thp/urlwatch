from nose.tools import eq_

from urlwatch.reporters import HtmlReporter

htmlreporter = HtmlReporter('', '', '', '')


def deleted_line():
    inp = '-Deleted line'
    out = ('<span style="color:red">-Deleted line</span>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def added_line():
    inp = '+Added line'
    out = ('<span style="color:green">+Added line</span>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def changes_line():
    '''Changes line'''
    inp = '@@ -1,1 +1,1 @@'
    out = ('<span style="background-color:whitesmoke">@@ -1,1 +1,1 @@</span>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def horizontal_ruler():
    '''Horizontal ruler (manually expanded since <hr> tag is used by urlwatch to separate jobs)'''
    inp = '+* * *'
    out = ('<span style="color:green">'
           '+--------------------------------------------------------------------------------'
           '</span>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def html_link():
    inp = '+[Link](https://example.com)'
    out = ('<span style="color:green">'
           '+<a style="font-family:inherit;color:inherit" target="_blank" href="https://example.com">Link</a>'
           '</span>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def html_image():
    inp = ' ![Image](https://example.com/picture.png "picture")'
    out = (' <img src="https://example.com/picture.png" alt="Image" title="picture" />')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def indented_text():
    inp = '   Indented text (replace leading spaces)'
    out = (' &nbsp;&nbsp;Indented text (replace leading spaces)')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def bullet_point_1():
    inp = '   * Bullet point level 1'
    out = (' &nbsp;&nbsp;● Bullet point level 1')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def bullet_point_2():
     inp = '     * Bullet point level 2'
    out = (' &nbsp;&nbsp;&nbsp;&nbsp;◾ Bullet point level 2')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def bullet_point_3():
     inp = '       * Bullet point level 3'
    out = (' &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;○ Bullet point level 3')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def bullet_point_4():
     inp = '         * Bullet point level 4'
    out = (' &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;○ Bullet point level 4')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def emphasis():
    inp = ' *emphasis*'
    out = (' <em>emphasis</em>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)


def strong():
    inp = ' **strong**'
    out = (' <strong>strong</strong>')
    eq_(''.join(list(htmlreporter._diff_to_html(inp, is_markdown=True))), out)

def strikethrough():
    inp = ' ~~strikethrough~~'
    out = (' <strike>strikethrough</strike>')
    eq_(''.join(l
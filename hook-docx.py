"""Runtime hook для doc-tpu — патчит путь к шаблонам docx в frozen bundle."""
import os
import sys


def _patch_docx_templates():
    """Monkey-patch docx template resolution for PyInstaller frozen bundles."""
    if not getattr(sys, 'frozen', False):
        return

    meipass = sys._MEIPASS

    try:
        import docx.parts.hdrftr as hdrftr

        def patched_footer_xml(cls):
            path = os.path.join(meipass, "docx", "templates", "default-footer.xml")
            with open(path, "rb") as f:
                return f.read()

        def patched_header_xml(cls):
            path = os.path.join(meipass, "docx", "templates", "default-header.xml")
            with open(path, "rb") as f:
                return f.read()

        hdrftr.FooterPart._default_footer_xml = classmethod(patched_footer_xml)
        hdrftr.HeaderPart._default_footer_xml = classmethod(patched_header_xml)
    except ImportError:
        pass


_patch_docx_templates()

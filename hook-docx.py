"""Runtime hook для PyInstaller — патчит docx templates для frozen bundle."""

import sys
import os


def _patch_docx_templates():
    """Патчит FooterPart и HeaderPart для работы в frozen bundle."""
    try:
        from docx.opc.part import Part
        from docx.oxml.ns import nsmap

        # Путь к docx templates в frozen bundle
        if hasattr(sys, '_MEIPASS'):
            templates_dir = os.path.join(sys._MEIPASS, 'docx', 'templates')
        else:
            return  # Не frozen — патч не нужен

        # Патчим FooterPart
        try:
            from docx.opc.parts.footer import FooterPart
            _original_footer_xml = FooterPart._default_footer_xml

            def _patched_footer_xml(cls):
                try:
                    return _original_footer_xml()
                except FileNotFoundError:
                    footer_path = os.path.join(templates_dir, 'default-footer.xml')
                    if os.path.exists(footer_path):
                        with open(footer_path, 'r', encoding='utf-8') as f:
                            return f.read()
                    raise

            FooterPart._default_footer_xml = classmethod(_patched_footer_xml)
        except ImportError:
            pass

        # Патчим HeaderPart
        try:
            from docx.opc.parts.header import HeaderPart
            _original_header_xml = HeaderPart._default_header_xml

            def _patched_header_xml(cls):
                try:
                    return _original_header_xml()
                except FileNotFoundError:
                    header_path = os.path.join(templates_dir, 'default-header.xml')
                    if os.path.exists(header_path):
                        with open(header_path, 'r', encoding='utf-8') as f:
                            return f.read()
                    raise

            HeaderPart._default_header_xml = classmethod(_patched_header_xml)
        except ImportError:
            pass

    except ImportError:
        pass


_patch_docx_templates()

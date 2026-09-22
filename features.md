Сейчас в этом проекте есть SKILL,
templatee.snj а мне хочется вот как раелизовать анную вешь это будет cli инструмент, со следующими параметрами 
-h, --help - будет помошь инмструмента
-p, --path - будет передаваться финальный путь файла куда экспортировать
-f, --format - поддержка генерации pdf, doc, pptx
-t, --template - это указание на файл формата .snj там будет описание какой структы должен файл получится
(соотведственно для презентации свой формат описательный, для одних форм отчета другие разложеные по папкм наверное это будет пока короткий или длинный отчет)
-i, --images - это функция будет пренимать пути до картинок котрые нужно вставить в отчет 
-b, --body  - это будет сам текстовое описание что и как надо встаивть(мне кажется тут будет свой конфиг котрый будет ссылочно картинку подтягивать)

Пример файлов передавемых в --body
```body.json
{
  "document": {
    "metadata": {
      "title": "Техническое задание",
      "author": "Иванов Иван",
      "created_at": "2026-09-21T13:21:00Z",
      "updated_at": "2026-09-21T13:25:00Z",
      "version": "1.0"
    },
    "settings": {
      "page_size": "A4",
      "orientation": "portrait",
      "margins": {
        "top": 20,
        "bottom": 20,
        "left": 30,
        "right": 15,
        "unit": "mm"
      }
    },
    "body": [
      {
        "type": "paragraph",
        "style": "Heading 1",
        "elements": [
          {
            "type": "text",
            "text": "1. Введение",
            "bold": true,
            "italic": false,
            "font_size": 18
          }
        ]
      },
      {
        "type": "paragraph",
        "style": "Normal",
        "elements": [
          {
            "type": "text",
            "text": "Это пример обычного абзаца текста. Некоторые слова в нем могут быть выделены ",
            "bold": false,
            "italic": false
          },
          {
            "type": "text",
            "text": "жирным шрифтом",
            "bold": true,
            "italic": false
          },
          {
            "type": "text",
            "text": " или курсивом.",
            "bold": false,
            "italic": true
          }
        ]
      },
      {
        "type": "list",
        "list_type": "bulleted",
        "items": [
          {
            "elements": [{ "type": "text", "text": "Элемент маркированного списка №1" }]
          },
          {
            "elements": [{ "type": "text", "text": "Элемент маркированного списка №2" }]
          }
        ]
      },
      {
        "type": "table",
        "rows": 2,
        "columns": 2,
        "content": [
          [
            { "elements": [{ "type": "text", "text": "Шапка таблицы 1", "bold": true }] },
            { "elements": [{ "type": "text", "text": "Шапка таблицы 2", "bold": true }] }
          ],
          [
            { "elements": [{ "type": "text", "text": "Ячейка А2" }] },
            { "elements": [{ "type": "text", "text": "Ячейка Б2" }] }
          ]
        ]
      },
      {
        "type": "image",
        "source": {},
        "alt_text": "Диаграмма архитектуры системы",
        "width": 600,
        "height": 400,
        "alignment": "center"
      }
    ]
  }
}
```

Пример template.snj
```
{
  "theme": {
    "typography": {
      "base_font": "Arial",
      "font_scale_unit": "pt"
    },
    "colors": {
      "primary": "#1A1A1A",
      "secondary": "#555555",
      "accent": "#0066CC"
    }
  },
  "styles": {
    "h1": {
      "font_size": 24,
      "bold": true,
      "color": "theme.colors.primary",
      "margin_bottom": 12
    },
    "body_text": {
      "font_size": 11,
      "line_height": 1.5,
      "color": "theme.colors.secondary",
      "text_align": "justify"
    },
    "list_item": {
      "font_size": 11,
      "color": "theme.colors.secondary",
      "indent": 15
    }
  },
  "image_presets": {
    "hero_banner": {
      "max_width_percent": 100,
      "aspect_ratio": "16:9",
      "border_radius": 8,
      "box_shadow": "0px 4px 10px rgba(0,0,0,0.15)",
      "responsive": true
    },
    "inline_thumbnail": {
      "fixed_width_px": 150,
      "fixed_height_px": 150,
      "object_fit": "cover",
      "border": {
        "width": 1,
        "style": "solid",
        "color": "#DDDDDD"
      },
      "float": "left",
      "margin": { "right": 10, "bottom": 10 }
    },
    "gallery_item": {
      "aspect_ratio": "1:1",
      "object_fit": "cover",
      "grid_span": 1,
      "zoom_on_hover": true
    }
  }
}
```

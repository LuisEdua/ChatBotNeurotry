catalog = {
    "version": "5.0",
    "screens": [
        {
            "id": "CATALOG",
            "title": "Catalogo",
            "terminal": True,
            "data": {
                "catalog_heading": {
                    "type": "string",
                    "__example__": "Elige los productos para realizar tu pedido"
                },
                "products": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "image": {}
                        }
                    },
                    "__example__": [
                        {"id": "1", "title": "Angular", "description": "$499.00", "image": "[image_base64]"},
                        {"id": "2", "title": "Vue", "description": "$499.00", "image": "[image_base64]"},
                        {"id": "3", "title": "React", "description": "$499.00", "image": "[image_base64]"},
                        {"id": "4", "title": "NextJS", "description": "$499.00", "image": "[image_base64]"},
                        {"id": "5", "title": "Node", "description": "$499.00", "image": "[image_base64]"}
                    ]
                }
            },
            "layout": {
                "type": "SingleColumnLayout",
                "children": [
                    {
                        "type": "Form",
                        "name": "form",
                        "children": [
                            {
                                "type": "CheckboxGroup",
                                "name": "selected_products",
                                "label": "${data.catalog_heading}",
                                "required": True,
                                "dataSource": "${data.products}"
                            },
                            {
                                "type": "Footer",
                                "label": "Continue",
                                "onClickAction": {
                                    "name": "complete",
                                    "payload": {
                                        "products": "${form.selected_products}"
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
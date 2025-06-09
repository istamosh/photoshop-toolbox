"""Module for processing PSD files and text layers."""

from datetime import datetime
from photoshop import Session
from .constants import LayerKind, Justification, TextSizing


class TextLayerProcessor:
    """Class for processing text layers in PSD files."""

    @staticmethod
    def update_text_layer(text_item, date, time_part, location_info=None):
        """Update text layer content and formatting."""
        try:
            # Format the date and time
            date_time = f"{date} {time_part}"

            # Prepare full text content
            if location_info:
                text_lines = [date_time] + location_info
            else:
                text_lines = [date_time]
            full_text = "\r".join(text_lines)

            # Update text content
            text_item.contents = full_text

            # Set text properties
            layer = text_item.parent
            doc = layer.parent
            min_dimension = min(doc.width, doc.height)

            # Calculate text size and positioning
            text_size = min_dimension * TextSizing.TEXT_SIZE_RATIO
            padding = min_dimension * TextSizing.PADDING_RATIO

            # Apply text formatting
            TextLayerProcessor._apply_text_formatting(text_item, text_size)
            TextLayerProcessor._position_text_layer(layer, doc, padding)

            return True
        except Exception as e:
            raise Exception(f"Failed to update text layer: {str(e)}")

    @staticmethod
    def _apply_text_formatting(text_item, text_size):
        """Apply text formatting properties."""
        text_item.size = text_size
        text_item.leading = text_size * TextSizing.LEADING_RATIO
        text_item.justification = Justification.RIGHT.value

    @staticmethod
    def _position_text_layer(layer, doc, padding):
        """Position the text layer in the document."""
        bounds = layer.bounds
        layer_width = bounds[2] - bounds[0]
        layer_height = bounds[3] - bounds[1]

        # Position in bottom-right corner
        new_x = doc.width - layer_width - padding
        new_y = doc.height - layer_height - padding

        # Calculate movement needed
        delta_x = new_x - bounds[0]
        delta_y = new_y - bounds[1]

        # Move layer
        layer.translate(delta_x, delta_y)

        # Verify and adjust if outside bounds
        updated_bounds = layer.bounds
        if updated_bounds[3] > doc.height or updated_bounds[2] > doc.width:
            adjust_x = max(0, updated_bounds[2] - doc.width + padding)
            adjust_y = max(0, updated_bounds[3] - doc.height + padding)
            layer.translate(-adjust_x, -adjust_y)


class DocumentProcessor:
    """Class for processing PSD documents."""

    @staticmethod
    def analyze_document(doc):
        """Analyze document properties."""
        return {
            "name": doc.name,
            "path": doc.fullName,
            "width": doc.width,
            "height": doc.height,
        }

    @staticmethod
    def check_type17_above_datetime(doc, datetime_layer):
        """Check for Type 17 layers above a datetime layer."""
        try:
            layers = list(doc.artLayers)
            for layer in reversed(layers):
                if layer == datetime_layer:
                    break
                elif layer.kind == LayerKind.TYPE_17.value:
                    return True, layer, "above"
            return False, None, None
        except Exception:
            return False, None, None

    @staticmethod
    def find_text_layers(doc):
        """Find text layers in document."""
        text_layers = []
        datetime_layers = []

        for layer in doc.artLayers:
            try:
                if hasattr(layer, "textItem") and layer.textItem:
                    text_content = layer.textItem.contents.strip()
                    if text_content:
                        if ("/" in text_content and "." in text_content) or (
                            "-" in text_content and ":" in text_content
                        ):
                            datetime_layers.append(layer)
                        else:
                            text_layers.append(layer)
            except:
                continue

        return text_layers, datetime_layers

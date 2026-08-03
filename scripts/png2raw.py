import struct
from typing import Tuple, Optional
from PyQt6.QtGui import QImage, QPainter, QColor
from PyQt6.QtCore import Qt, QByteArray

class PngToVeryfitRaw:
    
    @staticmethod
    def probe_image(path: str) -> Tuple[int, int, bool]:
        """
        Probe image to get dimensions and alpha status
        
        Args:
            path: Path to image file
            
        Returns:
            Tuple of (width, height, has_alpha)
        """
        img = QImage(path)
        if img.isNull():
            return 0, 0, False
        
        img = img.convertToFormat(QImage.Format.Format_RGBA8888)
        w = img.width()
        h = img.height()
        
        has_alpha = False
        for y in range(h):
            for x in range(w):
                px = img.pixelColor(x, y)
                if px.alpha() != 255:
                    has_alpha = True
                    break
            if has_alpha:
                break
        
        return w, h, has_alpha
    
    @staticmethod
    def pack_rgb565(r: int, g: int, b: int) -> int:
        """
        Pack RGB values to RGB565 format
        
        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)
            
        Returns:
            16-bit RGB565 value
        """
        r5 = (r >> 3) & 0x1F
        g6 = (g >> 2) & 0x3F
        b5 = (b >> 3) & 0x1F
        return (r5 << 11) | (g6 << 5) | b5
    
    @staticmethod
    def convert_auto(path: str, force_opaque_preview: bool = False) -> bytes:
        """
        Convert image to VeryFit RAW format (auto-detects alpha)
        
        Args:
            path: Path to image file
            force_opaque_preview: If True, force opaque mode (no alpha)
            
        Returns:
            RAW format bytes, or empty bytes on failure
        """
        img = QImage(path)
        if img.isNull():
            return b''
        
        img = img.convertToFormat(QImage.Format.Format_RGBA8888)
        w = img.width()
        h = img.height()
        
        # Detect alpha channel
        has_alpha_channel = False
        if not force_opaque_preview:
            for y in range(h):
                for x in range(w):
                    if img.pixelColor(x, y).alpha() != 255:
                        has_alpha_channel = True
                        break
                if has_alpha_channel:
                    break
        
        # RGB565 data (big-endian)
        rgb565 = bytearray(w * h * 2)
        idx = 0
        row_bytes = (w + 1) // 2
        alpha_a4 = bytearray(row_bytes * h)

        for y in range(h):
            row_offset = y * row_bytes
            out_idx = row_offset

            for x in range(0, w, 2):
                a0 = img.pixelColor(x, y).alpha()
                a0_4 = (a0 * 15) // 255

                a1_4 = 0
                if x + 1 < w:
                    a1 = img.pixelColor(x + 1, y).alpha()
                    a1_4 = (a1 * 15) // 255

                alpha_a4[out_idx] = (a0_4 << 4) | a1_4
                out_idx += 1
        
        # Alpha 4-bit (2 pixels per byte)
        alpha_a4 = bytearray()
        if has_alpha_channel and not force_opaque_preview:
            row_bytes = (w + 1) // 2
            alpha_a4 = bytearray(row_bytes * h)
            alpha_a4 = bytearray(row_bytes)
            
            out_idx = 0
            for y in range(h):
                for x in range(0, w, 2):
                    a0 = img.pixelColor(x, y).alpha()
                    a0_4 = (a0 * 15) // 255
                    
                    a1_4 = 0
                    if x + 1 < w:
                        a1 = img.pixelColor(x + 1, y).alpha()
                        a1_4 = (a1 * 15) // 255
                        
                    print(f"Image: {path}")
                    print(f"Width={w}, Height={h}")
                    print(f"row_bytes={(w + 1) // 2}")
                    print(f"Allocated={len(alpha_a4)}")
                    print(f"Writing index={out_idx}")
                    
                    alpha_a4[out_idx] = (a0_4 << 4) | (a1_4 & 0x0F)
                    out_idx += 1
        
        # Build header (16 bytes)
        header = bytearray(16)
        
        # Magic: "RAW\0"
        header[0:4] = b'RAW\x00'
        
        # Width, height (little-endian)
        struct.pack_into('<H', header, 4, w)
        struct.pack_into('<H', header, 6, h)
        
        # Flags
        # opaque => 0x0085 => bytes [0x85, 0x00]
        # alpha  => 0x6685 => bytes [0x85, 0x66]
        if has_alpha_channel and not force_opaque_preview:
            header[8] = 0x85
            header[9] = 0x66
            rgb_size = w * h * 2
            struct.pack_into('<H', header, 12, rgb_size)
        else:
            header[8] = 0x85
            header[9] = 0x00
        
        # [10..11] 0x0000
        # [14..15] 0x0000 (already zero)
        
        # Build output
        out = bytearray(header)
        out.extend(rgb565)
        if has_alpha_channel and not force_opaque_preview:
            out.extend(alpha_a4)
        
        return bytes(out)
    
    @staticmethod
    def convert(img_path: str) -> bytes:
        """
        Convert image to VeryFit RAW format with alpha flattening on black
        
        Args:
            img_path: Path to image file
            
        Returns:
            RAW format bytes with padding, or empty bytes on failure
        """
        img = QImage(img_path)
        if img.isNull():
            print(f"PngToVeryfitRaw: Invalid image: {img_path}")
            return b''
        
        # Convert to ARGB32 for easy RGBA access
        if img.format() != QImage.Format.Format_ARGB32:
            img = img.convertToFormat(QImage.Format.Format_ARGB32)
        
        w = img.width()
        h = img.height()
        
        # Step 1: Create RGB565 buffer with alpha flattened on black
        rgb565 = bytearray(w * h * 2)
        
        for y in range(h):
            for x in range(w):
                px = img.pixelColor(x, y)
                r = px.red()
                g = px.green()
                b = px.blue()
                a = px.alpha()
                
                # Flatten alpha on black background
                if a < 255:
                    r = (r * a) // 255
                    g = (g * a) // 255
                    b = (b * a) // 255
                
                # Convert RGB888 -> RGB565
                r5 = r >> 3
                g6 = g >> 2
                b5 = b >> 3
                px16 = (r5 << 11) | (g6 << 5) | b5
                
                # VeryFit uses BIG-ENDIAN
                idx = (y * w + x) * 2
                rgb565[idx] = (px16 >> 8) & 0xFF      # High byte
                rgb565[idx + 1] = px16 & 0xFF         # Low byte
        
        # Step 2: Assemble RAW file
        out = bytearray()
        
        # RAW header (8 bytes)
        out.extend(b'RAW\x00')
        
        # Width and height (little-endian)
        out.extend(struct.pack('<H', w))
        out.extend(struct.pack('<H', h))
        
        # RGB565 data
        out.extend(rgb565)
        
        # Step 3: Padding with zeros to expected size
        # VeryFit reference uses 14816 bytes for 74x80 images
        expected_size = 14816  # Fixed size observed
        actual_size = len(out)  # 8 + (74×80×2) = 11848
        
        if actual_size < expected_size:
            padding = expected_size - actual_size
            out.extend(b'\x00' * padding)
            print(f"PngToVeryfitRaw: Added {padding} bytes padding")
        
        print(f"PngToVeryfitRaw: Image: {img_path}, Dimensions: {w}×{h}, "
              f"RGB565: {len(rgb565)} bytes, Total (with padding): {len(out)} bytes")
        
        return bytes(out)
    
    @staticmethod
    def convert_with_canvas(img_path: str, canvas_w: int, canvas_h: int) -> bytes:
        """
        Convert image to VeryFit RAW format with canvas rendering
        
        Args:
            img_path: Path to image file
            canvas_w: Canvas width
            canvas_h: Canvas height
            
        Returns:
            RAW format bytes with canvas rendering
        """
        # Load source image
        src = QImage(img_path)
        if src.isNull():
            print(f"convertWithCanvas: Invalid image: {img_path}")
            return b''
        
        if src.format() != QImage.Format.Format_ARGB32:
            src = src.convertToFormat(QImage.Format.Format_ARGB32)
        
        w_src = src.width()
        h_src = src.height()
        
        if w_src > canvas_w or h_src > canvas_h:
            print(f"convertWithCanvas: Source larger than canvas: {img_path}, "
                  f"src: {w_src}x{h_src}, canvas: {canvas_w}x{canvas_h}")
        
        # Final canvas ARGB32
        canvas = QImage(canvas_w, canvas_h, QImage.Format.Format_ARGB32)
        canvas.fill(Qt.GlobalColor.transparent)
        
        # Paint source onto canvas
        painter = QPainter(canvas)
        painter.drawImage(0, 0, src)
        painter.end()
        
        # Check if alpha is needed
        need_a4 = False
        for y in range(canvas_h):
            for x in range(canvas_w):
                if canvas.pixelColor(x, y).alpha() < 255:
                    need_a4 = True
                    break
            if need_a4:
                break
        
        # Generate RGB565 plane (2 bytes/pixel)
        rgb565_len = canvas_w * canvas_h * 2
        rgb565 = bytearray(rgb565_len)
        
        for y in range(canvas_h):
            for x in range(canvas_w):
                px = canvas.pixelColor(x, y)
                r = px.red()
                g = px.green()
                b = px.blue()
                
                r5 = r >> 3
                g6 = g >> 2
                b5 = b >> 3
                px16 = (r5 << 11) | (g6 << 5) | b5
                
                # VeryFit: BIG-ENDIAN (high byte first)
                idx = (y * canvas_w + x) * 2
                rgb565[idx] = (px16 >> 8) & 0xFF      # High byte
                rgb565[idx + 1] = px16 & 0xFF         # Low byte
        
        # Generate A4 alpha plane (4 bits/pixel, 2 pixels/byte)
        a4 = bytearray()
        if need_a4:
            # Calculate exactly how many bytes we need
            a4_row_bytes = (canvas_w + 1) // 2
            a4_total_bytes = a4_row_bytes * canvas_h
            a4 = bytearray(a4_total_bytes)
            
            row_bytes = (canvas_w + 1) // 2
            a4 = bytearray(row_bytes * canvas_h)

            a4_idx = 0
            for y in range(canvas_h):
                for x in range(0, canvas_w, 2):
                    a0 = canvas.pixelColor(x, y).alpha()
                    a0_4 = (a0 + 8) // 17

                    a1_4 = 0
                    if x + 1 < canvas_w:
                        a1 = canvas.pixelColor(x + 1, y).alpha()
                        a1_4 = (a1 + 8) // 17

                    a4[a4_idx] = (a0_4 << 4) | (a1_4 & 0x0F)
                    a4_idx += 1
                    
                    # Pack two 4-bit values into one byte
                    if a4_idx < len(a4):
                        a4[a4_idx] = (a0_4 << 4) | (a1_4 & 0x0F)
                        a4_idx += 1
        
        # Build VeryFit header (16 bytes)
        flags = 0x6685 if need_a4 else 0x0085
        crc = 0x0000
        rgb_len_field = rgb565_len if need_a4 else 0x0000
        zero = 0x0000
        
        out = bytearray()
        
        # "RAW\0"
        out.extend(b'RAW\x00')
        
        # Width, height (little-endian)
        out.extend(struct.pack('<H', canvas_w))
        out.extend(struct.pack('<H', canvas_h))
        
        # Flags, CRC, RGB length, zero
        out.extend(struct.pack('<H', flags))
        out.extend(struct.pack('<H', crc))
        out.extend(struct.pack('<H', rgb_len_field))
        out.extend(struct.pack('<H', zero))
        
        # Add pixels + alpha
        out.extend(rgb565)
        if need_a4:
            out.extend(a4)
        
        return bytes(out)
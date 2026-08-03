import os
import json
import struct
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from png2raw import PngToVeryfitRaw


class ImageInfo:
    def __init__(self):
        self.file_name = ""
        self.base_name = ""
        self.parent_name = ""
        self.abs_path = ""
        self.width = 0
        self.height = 0
        self.has_alpha = False


class EntryToPack:
    def __init__(self):
        self.logical_name = ""
        self.abs_path = ""
        self.is_image = False
        self.force_opaque_preview = False


class BankInfo:
    def __init__(self):
        self.bank_name = ""
        self.glyphs: Dict[int, int] = {}  # glyph_id -> image_index


def scan_all_images(src_dir: str) -> List[ImageInfo]:
    """Scan all images in directory"""
    out = []
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith(('.png', '.bmp')):
                abs_path = os.path.join(root, file)
                w, h, has_alpha = PngToVeryfitRaw.probe_image(abs_path)
                if w > 0:
                    info = ImageInfo()
                    info.file_name = file
                    info.base_name = os.path.splitext(file)[0]
                    info.parent_name = os.path.basename(root)
                    info.abs_path = abs_path
                    info.width = w
                    info.height = h
                    info.has_alpha = has_alpha
                    out.append(info)
    return out


def parse_iwf_json(src_dir: str) -> Tuple[str, str, bool]:
    """Parse iwf.json to extract bkground and preview"""
    iwf_path = os.path.join(src_dir, "iwf.json")
    if not os.path.exists(iwf_path):
        return "", "", False
    
    try:
        with open(iwf_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        background = data.get("bkground", "")
        preview = data.get("preview", "")
        return background, preview, bool(background or preview)
    except:
        return "", "", False


def read_font_order(src_dir: str) -> List[str]:
    """Read font.json to get bank order"""
    font_path = os.path.join(src_dir, "font.json")
    if not os.path.exists(font_path):
        return []
    
    try:
        with open(font_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        order = []
        for item in data.get("item", []):
            name = item.get("name", "").strip()
            if name:
                order.append(name)
        return order
    except:
        return []


def build_banks(all_images: List[ImageInfo], src_dir: str) -> Dict[str, BankInfo]:
    """Build bank information from images"""
    banks = {}
    root_name = os.path.basename(src_dir)
    
    for i, img in enumerate(all_images):
        if not img.parent_name or img.parent_name == root_name or img.parent_name == ".":
            continue
        
        try:
            glyph_id = int(img.base_name)
        except ValueError:
            continue
        
        bank = banks.get(img.parent_name, BankInfo())
        bank.bank_name = img.parent_name
        bank.glyphs[glyph_id] = i
        banks[img.parent_name] = bank
    
    return banks


# General order from VeryFit reference
GENERAL_ORDER = [
    26, 24, 2, 11, 37, 6, 38, 15, 21, 28, 36, 29,
    16, 3, 10, 40, 4, 33, 39, 35, 18, 34, 22, 31,
    27, 9, 7, 1, 19, 25, 32, 20, 14, 0, 23, 12,
    30, 5, 17, 13, 8
]


def emit_bank_in_order(bank_name: str, bank: BankInfo, all_images: List[ImageInfo]) -> List[EntryToPack]:
    """Emit bank entries in order"""
    result = []
    for glyph_id in GENERAL_ORDER:
        if glyph_id not in bank.glyphs:
            continue
        
        img_idx = bank.glyphs[glyph_id]
        logical = f"{bank_name}_{glyph_id}"
        
        entry = EntryToPack()
        entry.logical_name = logical
        entry.abs_path = all_images[img_idx].abs_path
        entry.is_image = True
        entry.force_opaque_preview = False
        result.append(entry)
    
    return result


WEEK_ORDER = ["tue", "fri", "sat", "sun", "thur", "wed", "mon"]


def emit_week_bank(all_images: List[ImageInfo]) -> List[EntryToPack]:
    """Emit week bank entries"""
    result = []
    for day in WEEK_ORDER:
        want_file = f"en_{day}.png"
        logical = f"week_en_{day}"
        
        found_idx = -1
        for i, img in enumerate(all_images):
            if img.parent_name.lower() == "week" and img.file_name.lower() == want_file:
                found_idx = i
                break
        
        if found_idx >= 0:
            entry = EntryToPack()
            entry.logical_name = logical
            entry.abs_path = all_images[found_idx].abs_path
            entry.is_image = True
            entry.force_opaque_preview = False
            result.append(entry)
    
    return result


MONTH_ORDER = ["nov", "oct", "dec", "may", "june", "apr", "jan", 
               "feb", "sept", "july", "mar", "aug"]


def emit_month_bank(all_images: List[ImageInfo]) -> List[EntryToPack]:
    """Emit month bank entries"""
    result = []
    for month in MONTH_ORDER:
        want_file = f"en_{month}.png"
        logical = f"month_en_{month}"
        
        found_idx = -1
        for i, img in enumerate(all_images):
            if img.parent_name.lower() == "month" and img.file_name.lower() == want_file:
                found_idx = i
                break
        
        if found_idx >= 0:
            entry = EntryToPack()
            entry.logical_name = logical
            entry.abs_path = all_images[found_idx].abs_path
            entry.is_image = True
            entry.force_opaque_preview = False
            result.append(entry)
    
    return result


def build_ordered_entry_list(src_dir: str) -> List[EntryToPack]:
    """Build ordered list of entries for IWF"""
    result = []
    
    all_images = scan_all_images(src_dir)
    background, preview, _ = parse_iwf_json(src_dir)
    font_order = read_font_order(src_dir)
    
    # Add iwf.json and font.json
    for name in ["iwf.json", "font.json"]:
        path = os.path.join(src_dir, name)
        if os.path.exists(path):
            entry = EntryToPack()
            entry.logical_name = name
            entry.abs_path = path
            entry.is_image = False
            entry.force_opaque_preview = False
            result.append(entry)
    
    # Parse iwf.json for referenced images
    referenced = set()
    iwf_path = os.path.join(src_dir, "iwf.json")
    if os.path.exists(iwf_path):
        try:
            with open(iwf_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Root keys
            for key in ["bkground", "preview"]:
                if key in data and data[key]:
                    referenced.add(data[key])
            
            # Item keys
            item_keys = ["hour", "minute", "second", "bg", "animaicon", "progress"]
            for item in data.get("item", []):
                for key in item_keys:
                    if key in item and item[key]:
                        referenced.add(item[key])
        except:
            pass
    
    # Add background
    if background and background in referenced:
        for i, img in enumerate(all_images):
            if img.file_name.lower() == background.lower():
                entry = EntryToPack()
                entry.logical_name = img.file_name
                entry.abs_path = img.abs_path
                entry.is_image = True
                entry.force_opaque_preview = False
                result.append(entry)
                referenced.remove(background)
                break
    
    # Add preview
    if preview and preview in referenced:
        for i, img in enumerate(all_images):
            if img.file_name.lower() == preview.lower():
                entry = EntryToPack()
                entry.logical_name = img.file_name
                entry.abs_path = img.abs_path
                entry.is_image = True
                entry.force_opaque_preview = True
                result.append(entry)
                referenced.remove(preview)
                break
    
    # Add remaining referenced images
    for img_name in referenced:
        for i, img in enumerate(all_images):
            if (img.parent_name and img.parent_name != "." and 
                img.parent_name != os.path.basename(src_dir)):
                continue
            if img.file_name.lower() == img_name.lower():
                entry = EntryToPack()
                entry.logical_name = img.file_name
                entry.abs_path = img.abs_path
                entry.is_image = True
                entry.force_opaque_preview = False
                result.append(entry)
                break
    
    # Add banks
    banks = build_banks(all_images, src_dir)
    
    for bank_name in font_order:
        if bank_name.lower() == "week":
            result.extend(emit_week_bank(all_images))
        elif bank_name.lower() == "month":
            result.extend(emit_month_bank(all_images))
        elif bank_name in banks:
            result.extend(emit_bank_in_order(bank_name, banks[bank_name], all_images))
    
    return result


def write_name_32(name: str) -> bytes:
    """Write 32-byte null-terminated name"""
    name_bytes = name.encode('latin-1')[:31]
    return name_bytes.ljust(32, b'\x00')


def create_iwf_from_folder(src_dir: str, out_path: str) -> bool:
    """Create IWF file from folder"""
    entries = build_ordered_entry_list(src_dir)
    entry_count = len(entries)
    
    # Convert each entry
    built = []
    running_offset = 0
    
    for entry in entries:
        if entry.is_image:
            data = PngToVeryfitRaw.convert_auto(entry.abs_path, entry.force_opaque_preview)
        else:
            with open(entry.abs_path, 'rb') as f:
                data = f.read()
        
        built.append({
            'meta': entry,
            'data': data,
            'local_offset': running_offset,
            'size': len(data)
        })
        running_offset += len(data)
    
    # Build header and index
    header_size = 8
    index_size = entry_count * 40
    base_offset = header_size + index_size
    
    header_and_index = bytearray(base_offset)
    
    # Magic: "iwf\0"
    header_and_index[0:4] = b'iwf\x00'
    header_and_index[4] = 0x01  # version
    header_and_index[5] = 0x00
    header_and_index[6] = entry_count & 0xFF
    header_and_index[7] = (entry_count >> 8) & 0xFF
    
    idx_ptr = 8
    for b in built:
        # Name (32 bytes)
        name_bytes = write_name_32(b['meta'].logical_name)
        header_and_index[idx_ptr:idx_ptr + 32] = name_bytes
        idx_ptr += 32
        
        # Offset (4 bytes, little-endian)
        abs_off = base_offset + b['local_offset']
        struct.pack_into('<I', header_and_index, idx_ptr, abs_off)
        idx_ptr += 4
        
        # Size (4 bytes, little-endian)
        struct.pack_into('<I', header_and_index, idx_ptr, b['size'])
        idx_ptr += 4
    
    # Build final output
    final_data = bytearray(header_and_index)
    for b in built:
        final_data.extend(b['data'])
    
    # Write to file
    try:
        with open(out_path, 'wb') as f:
            f.write(final_data)
        return True
    except:
        return False
    
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create IWF from folder")
    parser.add_argument("src_dir", help="Source directory containing images and iwf.json")
    parser.add_argument("out_path", help="Output IWF file path")
    
    args = parser.parse_args()
    
    success = create_iwf_from_folder(args.src_dir, args.out_path)
    if success:
        print(f"Successfully created IWF: {args.out_path}")
    else:
        print(f"Failed to create IWF: {args.out_path}")
        
if __name__ == "__main__":
    main()

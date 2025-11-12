import streamlit as st
import pickle
from collections import Counter
from typing import Optional, Dict, Tuple
import io


class MinHeap:
    """Min Heap implementation for Huffman encoding"""
    
    def __init__(self):
        self.heap = []
    
    def parent(self, i: int) -> int:
        return (i - 1) // 2
    
    def left_child(self, i: int) -> int:
        return 2 * i + 1
    
    def right_child(self, i: int) -> int:
        return 2 * i + 2
    
    def swap(self, i: int, j: int):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
    
    def insert(self, item):
        self.heap.append(item)
        self._heapify_up(len(self.heap) - 1)
    
    def _heapify_up(self, i: int):
        parent = self.parent(i)
        if i > 0 and self.heap[i].freq < self.heap[parent].freq:
            self.swap(i, parent)
            self._heapify_up(parent)
    
    def extract_min(self):
        if len(self.heap) == 0:
            return None
        if len(self.heap) == 1:
            return self.heap.pop()
        
        min_item = self.heap[0]
        self.heap[0] = self.heap.pop()
        self._heapify_down(0)
        return min_item
    
    def _heapify_down(self, i: int):
        min_idx = i
        left = self.left_child(i)
        right = self.right_child(i)
        
        if left < len(self.heap) and self.heap[left].freq < self.heap[min_idx].freq:
            min_idx = left
        if right < len(self.heap) and self.heap[right].freq < self.heap[min_idx].freq:
            min_idx = right
        
        if min_idx != i:
            self.swap(i, min_idx)
            self._heapify_down(min_idx)
    
    def size(self) -> int:
        return len(self.heap)


class HuffmanNode:
    """Node for Huffman tree"""
    
    def __init__(self, char: Optional[str], freq: int):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None


class HuffmanEncoder:
    """Huffman encoding implementation"""
    
    def __init__(self):
        self.root = None
        self.codes = {}
    
    def build_tree(self, text: str) -> HuffmanNode:
        """Build Huffman tree from text"""
        if not text:
            return None
        
        # Count character frequencies
        freq_map = Counter(text)
        
        # Create min heap
        heap = MinHeap()
        for char, freq in freq_map.items():
            heap.insert(HuffmanNode(char, freq))
        
        # Build tree
        while heap.size() > 1:
            left = heap.extract_min()
            right = heap.extract_min()
            
            merged = HuffmanNode(None, left.freq + right.freq)
            merged.left = left
            merged.right = right
            
            heap.insert(merged)
        
        self.root = heap.extract_min()
        return self.root
    
    def _generate_codes(self, node: HuffmanNode, code: str = ""):
        """Generate Huffman codes for each character"""
        if node is None:
            return
        
        if node.char is not None:
            self.codes[node.char] = code if code else "0"
            return
        
        self._generate_codes(node.left, code + "0")
        self._generate_codes(node.right, code + "1")
    
    def encode(self, text: str) -> Tuple[str, Dict[str, str]]:
        """Encode text using Huffman coding"""
        if not text:
            return "", {}
        
        self.build_tree(text)
        self._generate_codes(self.root)
        
        encoded = "".join(self.codes[char] for char in text)
        return encoded, self.codes
    
    def decode(self, encoded: str, root: HuffmanNode) -> str:
        """Decode encoded text using Huffman tree"""
        if not encoded or root is None:
            return ""
        
        decoded = []
        current = root
        
        for bit in encoded:
            if bit == "0":
                current = current.left
            else:
                current = current.right
            
            if current.char is not None:
                decoded.append(current.char)
                current = root
        
        return "".join(decoded)


class FileCompressor:
    """File compression using Huffman encoding"""
    
    def __init__(self):
        self.encoder = HuffmanEncoder()
    
    def compress(self, text: str) -> bytes:
        """Compress text and return binary data"""
        encoded_text, codes = self.encoder.encode(text)
        
        # Convert binary string to bytes
        padding = 8 - len(encoded_text) % 8
        encoded_text += "0" * padding
        
        byte_array = bytearray()
        for i in range(0, len(encoded_text), 8):
            byte = encoded_text[i:i+8]
            byte_array.append(int(byte, 2))
        
        # Store tree and padding info
        compressed_data = {
            'tree': self.encoder.root,
            'data': bytes(byte_array),
            'padding': padding,
            'original_length': len(text)
        }
        
        return pickle.dumps(compressed_data)
    
    def decompress(self, compressed: bytes) -> str:
        """Decompress binary data back to text"""
        compressed_data = pickle.loads(compressed)
        
        tree = compressed_data['tree']
        data = compressed_data['data']
        padding = compressed_data['padding']
        
        # Convert bytes back to binary string
        bit_string = ""
        for byte in data:
            bit_string += format(byte, '08b')
        
        # Remove padding
        bit_string = bit_string[:-padding] if padding else bit_string
        
        # Decode
        return self.encoder.decode(bit_string, tree)


# Streamlit UI
def main():
    st.set_page_config(page_title="Huffman Text Compressor", layout="centered")
    
    st.title("📦 Huffman Text Compressor")
    
    # Tab selection
    tab1, tab2 = st.tabs(["Compress", "Decompress"])
    
    # Compression tab
    with tab1:
        st.write("Upload a text file to compress it using Huffman encoding")
        
        uploaded_file = st.file_uploader("Choose a text file", type=['txt'], key="compress")
        
        if uploaded_file is not None:
            # Read file
            text = uploaded_file.read().decode('utf-8')
            original_size = len(text.encode('utf-8'))
            
            st.success(f"File uploaded: {uploaded_file.name}")
            st.info(f"Original size: {original_size:,} bytes")
            
            # Compress
            with st.spinner("Compressing..."):
                compressor = FileCompressor()
                compressed_data = compressor.compress(text)
                compressed_size = len(compressed_data)
            
            # Show results
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Original Size", f"{original_size:,} bytes")
            with col2:
                st.metric("Compressed Size", f"{compressed_size:,} bytes")
            with col3:
                st.metric("Compression Ratio", f"{compression_ratio:.2f}%")
            
            # Download button
            st.download_button(
                label="⬇️ Download Compressed File",
                data=compressed_data,
                file_name=f"{uploaded_file.name}.huff",
                mime="application/octet-stream"
            )
            
            st.divider()
            
            # Preview
            with st.expander("Preview original text (first 500 characters)"):
                st.text(text[:500] + ("..." if len(text) > 500 else ""))
    
    # Decompression tab
    with tab2:
        st.write("Upload a compressed .huff file to decompress it back to text")
        
        compressed_file = st.file_uploader("Choose a .huff file", type=['huff'], key="decompress")
        
        if compressed_file is not None:
            compressed_data = compressed_file.read()
            compressed_size = len(compressed_data)
            
            st.success(f"File uploaded: {compressed_file.name}")
            st.info(f"Compressed size: {compressed_size:,} bytes")
            
            # Decompress
            with st.spinner("Decompressing..."):
                try:
                    compressor = FileCompressor()
                    decompressed_text = compressor.decompress(compressed_data)
                    decompressed_size = len(decompressed_text.encode('utf-8'))
                    
                    st.success("Decompression successful!")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Compressed Size", f"{compressed_size:,} bytes")
                    with col2:
                        st.metric("Decompressed Size", f"{decompressed_size:,} bytes")
                    
                    # Download button
                    original_name = compressed_file.name.replace('.huff', '')
                    st.download_button(
                        label="⬇️ Download Decompressed File",
                        data=decompressed_text,
                        file_name=original_name,
                        mime="text/plain"
                    )
                    
                    st.divider()
                    
                    # Preview
                    with st.expander("Preview decompressed text (first 500 characters)"):
                        st.text(decompressed_text[:500] + ("..." if len(decompressed_text) > 500 else ""))
                
                except Exception as e:
                    st.error(f"Error decompressing file: {str(e)}")
                    st.warning("Make sure this is a valid .huff file created by this compressor.")


if __name__ == "__main__":
    main()
"""
Generate a simple test audio file for end-to-end testing.
Creates a short WAV file with speech for testing the complete pipeline.
"""

import numpy as np
import wave
import os
from pathlib import Path

def generate_test_audio(filename: str = "test_audio.wav", duration: float = 5.0):
    """
    Generate a simple test audio file with synthetic speech-like patterns.
    
    Args:
        filename: Output filename
        duration: Duration in seconds
    """
    # Audio parameters
    sample_rate = 16000  # 16 kHz, common for speech
    amplitude = 0.3
    
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a simple speech-like pattern with multiple frequencies
    # Simulate formants and speech patterns
    f1 = 200  # Base frequency
    f2 = 800  # First formant
    f3 = 2400  # Second formant
    
    # Generate speech-like signal with modulation
    signal = (
        amplitude * np.sin(2 * np.pi * f1 * t) * np.exp(-t * 0.1) +
        amplitude * 0.5 * np.sin(2 * np.pi * f2 * t) * np.exp(-t * 0.2) +
        amplitude * 0.3 * np.sin(2 * np.pi * f3 * t) * np.exp(-t * 0.3)
    )
    
    # Add some variation to simulate speech patterns
    envelope = np.sin(2 * np.pi * 3 * t) * 0.3 + 0.7  # 3 Hz modulation
    signal = signal * envelope
    
    # Add some noise for realism
    noise = np.random.normal(0, 0.01, len(signal))
    signal = signal + noise
    
    # Normalize to prevent clipping
    signal = signal / np.max(np.abs(signal)) * 0.8
    
    # Convert to 16-bit PCM
    signal_int = (signal * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(signal_int.tobytes())
    
    print(f"Generated test audio file: {filename}")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: {sample_rate} Hz")
    print(f"File size: {os.path.getsize(filename)} bytes")

if __name__ == "__main__":
    # Generate test audio file
    test_file = Path("test_audio.wav")
    generate_test_audio(str(test_file))
    
    print(f"\nTest audio file created: {test_file.absolute()}")
    print("This file can be used for end-to-end testing of the audio processing pipeline.")

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { validateFile, validateImageDecoding, safeRevokeUrl } from './fileValidation';
import { appConfig } from '../config/appConfig';

describe('fileValidation utility', () => {
  it('accepts valid JPEG, PNG, and WebP images within 10MB', () => {
    const validJpg = new File(['dummy content'], 'photo.jpg', { type: 'image/jpeg' });
    const resultJpg = validateFile(validJpg);
    expect(resultJpg.isValid).toBe(true);
    expect(resultJpg.error).toBeNull();

    const validPng = new File(['dummy content'], 'face.png', { type: 'image/png' });
    const resultPng = validateFile(validPng);
    expect(resultPng.isValid).toBe(true);

    const validWebp = new File(['dummy content'], 'avatar.webp', { type: 'image/webp' });
    const resultWebp = validateFile(validWebp);
    expect(resultWebp.isValid).toBe(true);
  });

  it('rejects a null or undefined file', () => {
    const result = validateFile(null);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('No file selected');
  });

  it('rejects files exceeding the 10 MB maximum limit', () => {
    const largeSize = 11 * 1024 * 1024; // 11 MB
    const largeFile = new File([new ArrayBuffer(largeSize)], 'large_photo.jpg', { type: 'image/jpeg' });
    const result = validateFile(largeFile);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('exceeds the 10 MB maximum limit');
  });

  it('rejects unsupported MIME types', () => {
    const gifFile = new File(['dummy'], 'animation.gif', { type: 'image/gif' });
    const result = validateFile(gifFile);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Unsupported file type');

    const pdfFile = new File(['dummy'], 'report.pdf', { type: 'application/pdf' });
    const pdfResult = validateFile(pdfFile);
    expect(pdfResult.isValid).toBe(false);
  });

  it('rejects unsupported file extensions even if MIME type is spoofed', () => {
    const spoofedFile = new File(['dummy'], 'malicious.exe', { type: 'image/jpeg' });
    const result = validateFile(spoofedFile);
    expect(result.isValid).toBe(false);
    expect(result.error).toContain('Unsupported file extension');
  });

  it('validates image decoding and safely revokes URL', async () => {
    // Mock URL.createObjectURL and revokeObjectURL
    const revokeMock = vi.fn();
    const createMock = vi.fn().mockReturnValue('blob:mock-url');
    globalThis.URL.createObjectURL = createMock;
    globalThis.URL.revokeObjectURL = revokeMock;

    // Mock Image constructor
    const originalImage = globalThis.Image;
    globalThis.Image = class {
      constructor() {
        setTimeout(() => {
          this.naturalWidth = 512;
          this.naturalHeight = 512;
          if (this.onload) this.onload();
        }, 10);
      }
    };

    const file = new File(['pixels'], 'test.png', { type: 'image/png' });
    const decodeResult = await validateImageDecoding(file);

    expect(decodeResult.isValid).toBe(true);
    expect(decodeResult.width).toBe(512);
    expect(decodeResult.height).toBe(512);
    expect(revokeMock).toHaveBeenCalledWith('blob:mock-url');

    globalThis.Image = originalImage;
  });

  it('rejects corrupted images that fail image decoding', async () => {
    const revokeMock = vi.fn();
    globalThis.URL.createObjectURL = vi.fn().mockReturnValue('blob:corrupted-url');
    globalThis.URL.revokeObjectURL = revokeMock;

    const originalImage = globalThis.Image;
    globalThis.Image = class {
      constructor() {
        setTimeout(() => {
          if (this.onerror) this.onerror(new Error('Corrupted image'));
        }, 10);
      }
    };

    const file = new File(['corrupt-data'], 'corrupted.jpg', { type: 'image/jpeg' });
    const decodeResult = await validateImageDecoding(file);

    expect(decodeResult.isValid).toBe(false);
    expect(decodeResult.error).toContain('corrupted');
    expect(revokeMock).toHaveBeenCalledWith('blob:corrupted-url');

    globalThis.Image = originalImage;
  });

  it('safeRevokeUrl safely ignores non-blob URLs and catches errors', () => {
    const revokeMock = vi.fn();
    globalThis.URL.revokeObjectURL = revokeMock;

    safeRevokeUrl('https://example.com/image.png');
    expect(revokeMock).not.toHaveBeenCalled();

    safeRevokeUrl('blob:http://localhost/123');
    expect(revokeMock).toHaveBeenCalledWith('blob:http://localhost/123');
  });
});

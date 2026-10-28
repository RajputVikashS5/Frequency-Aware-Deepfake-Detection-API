import { appConfig } from '../config/appConfig';

/**
 * Validates file size, extension, and MIME type.
 * @param {File} file 
 * @returns {{ isValid: boolean, error: string | null }}
 */
export function validateFile(file) {
  if (!file) {
    return { isValid: false, error: 'No file selected.' };
  }

  // 1. Check file size
  if (file.size > appConfig.maxFileSizeBytes) {
    const maxMb = (appConfig.maxFileSizeBytes / (1024 * 1024)).toFixed(0);
    return {
      isValid: false,
      error: `File size exceeds the ${maxMb} MB maximum limit (${(file.size / (1024 * 1024)).toFixed(1)} MB uploaded).`,
    };
  }

  // 2. Check MIME type
  if (!appConfig.allowedMimeTypes.includes(file.type)) {
    return {
      isValid: false,
      error: `Unsupported file type (${file.type || 'unknown'}). Please upload a JPG, PNG, or WebP image.`,
    };
  }

  // 3. Check extension
  const extension = '.' + file.name.split('.').pop().toLowerCase();
  if (!appConfig.allowedExtensions.includes(extension)) {
    return {
      isValid: false,
      error: `Unsupported file extension (${extension}). Allowed: ${appConfig.allowedExtensions.join(', ')}.`,
    };
  }

  return { isValid: true, error: null };
}

/**
 * Validates that an image file can be decoded without corruption.
 * Extracts image natural dimensions and safely revokes the temporary Object URL.
 * @param {File} file 
 * @returns {Promise<{ isValid: boolean, width: number, height: number, error: string | null }>}
 */
export function validateImageDecoding(file) {
  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();

    img.onload = () => {
      const width = img.naturalWidth;
      const height = img.naturalHeight;
      URL.revokeObjectURL(objectUrl);

      if (width === 0 || height === 0) {
        resolve({
          isValid: false,
          width: 0,
          height: 0,
          error: 'The image has invalid dimensions or failed decoding.',
        });
      } else {
        resolve({
          isValid: true,
          width,
          height,
          error: null,
        });
      }
    };

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      resolve({
        isValid: false,
        width: 0,
        height: 0,
        error: 'The image file appears to be corrupted and could not be decoded.',
      });
    };

    img.src = objectUrl;
  });
}

/**
 * Safely revokes an object URL if it is a blob URL.
 * @param {string} url 
 */
export function safeRevokeUrl(url) {
  if (url && typeof url === 'string' && url.startsWith('blob:')) {
    try {
      URL.revokeObjectURL(url);
    } catch (e) {
      // Ignore cleanup error
    }
  }
}

/**
 * Reads an image into a data URL for the current browser session only.
 * Callers must not persist the returned value to localStorage or a backend.
 * @param {File} file
 * @returns {Promise<string>}
 */
export function readImageForSession(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('The selected image could not be prepared for preview.'));
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '');
    reader.readAsDataURL(file);
  });
}

import '@testing-library/jest-dom';

// Polyfill or mock canvas context in jsdom for tests
if (typeof HTMLCanvasElement !== 'undefined') {
  HTMLCanvasElement.prototype.getContext = () => ({
    fillRect: () => {},
    clearRect: () => {},
    getImageData: (x, y, w, h) => ({ data: new Array(w * h * 4) }),
    putImageData: () => {},
    createImageData: () => [],
    setTransform: () => {},
    drawImage: () => {},
    save: () => {},
    fillText: () => {},
    restore: () => {},
    beginPath: () => {},
    moveTo: () => {},
    lineTo: () => {},
    closePath: () => {},
    stroke: () => {},
    fill: () => {},
    arc: () => {},
    createRadialGradient: () => ({
      addColorStop: () => {},
    }),
  });

  HTMLCanvasElement.prototype.toDataURL = () => 'data:image/jpeg;base64,mockCanvasData';
}

// In jsdom, Image does not automatically fire onload when src is assigned
if (typeof HTMLImageElement !== 'undefined') {
  Object.defineProperty(HTMLImageElement.prototype, 'naturalWidth', {
    get() { return 512; },
    configurable: true,
  });
  Object.defineProperty(HTMLImageElement.prototype, 'naturalHeight', {
    get() { return 512; },
    configurable: true,
  });

  const originalSrcDesc = Object.getOwnPropertyDescriptor(HTMLImageElement.prototype, 'src');
  Object.defineProperty(HTMLImageElement.prototype, 'src', {
    set(value) {
      if (originalSrcDesc && originalSrcDesc.set) {
        originalSrcDesc.set.call(this, value);
      } else {
        this._src = value;
      }
      setTimeout(() => {
        if (typeof this.onload === 'function') {
          this.onload();
        }
      }, 5);
    },
    get() {
      if (originalSrcDesc && originalSrcDesc.get) {
        return originalSrcDesc.get.call(this);
      }
      return this._src || '';
    },
    configurable: true,
  });
}

import { apiClient } from './client';
import type {
  MediaUploadInitRequest,
  MediaUploadInitResponse,
  MediaUploadCompleteResponse,
  MediaPlaybackResponse,
  MediaDownloadResponse,
} from '../types/media';

export const mediaService = {
  /**
   * Request pre-signed direct upload ticket and server-generated key from backend.
   */
  async initiateUpload(payload: MediaUploadInitRequest): Promise<MediaUploadInitResponse> {
    return apiClient<MediaUploadInitResponse>('/api/v1/media/uploads', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /**
   * Direct browser-to-storage transfer via pre-signed PUT URL with progress tracking.
   * If in local mock mode (starts with http://testserver or mock-storage), handles via proxy.
   */
  directUpload(
    uploadUrl: string,
    file: File | Blob,
    contentType: string,
    onProgress?: (percent: number) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      // In local dev/mock test environments where storage URL is relative or mock:
      let targetUrl = uploadUrl;
      if (uploadUrl.includes('/mock-storage.edtech.local/')) {
        const parts = uploadUrl.split('/mock-storage.edtech.local/');
        if (parts.length > 1) {
          // Point to local mock upload route
          const keyWithBucket = parts[1].split('?')[0];
          // Strip bucket prefix
          const bucketIndex = keyWithBucket.indexOf('/');
          const objectKey = bucketIndex !== -1 ? keyWithBucket.substring(bucketIndex + 1) : keyWithBucket;
          targetUrl = `/api/v1/media/mock-storage/${objectKey}`;
        }
      }

      const xhr = new XMLHttpRequest();
      xhr.open('PUT', targetUrl, true);
      xhr.setRequestHeader('Content-Type', contentType);

      if (xhr.upload && onProgress) {
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = Math.round((event.loaded / event.total) * 100);
            onProgress(percentComplete);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          if (onProgress) onProgress(100);
          resolve();
        } else {
          reject(new Error(`Object storage transfer failed with status ${xhr.status}: ${xhr.statusText}`));
        }
      };

      xhr.onerror = () => {
        reject(new Error('Network error during direct storage transfer'));
      };

      xhr.ontimeout = () => {
        reject(new Error('Upload transfer timed out'));
      };

      xhr.send(file);
    });
  },

  /**
   * Complete upload and trigger server-side magic byte and size verification.
   */
  async completeUpload(uploadId: string): Promise<MediaUploadCompleteResponse> {
    return apiClient<MediaUploadCompleteResponse>(`/api/v1/media/uploads/${uploadId}/complete`, {
      method: 'POST',
    });
  },

  /**
   * Request 30-minute signed playback URL for lecture video.
   */
  async getPlaybackUrl(lectureId: string): Promise<MediaPlaybackResponse> {
    return apiClient<MediaPlaybackResponse>(`/api/v1/media/assets/${lectureId}/play`, {
      method: 'GET',
    });
  },

  /**
   * Request 15-minute signed download URL for lecture notes or assignment attachments.
   */
  async getDownloadUrl(
    assetId: string,
    assetType: 'lecture_note' | 'submission_attachment'
  ): Promise<MediaDownloadResponse> {
    return apiClient<MediaDownloadResponse>(
      `/api/v1/media/assets/${assetId}/download?asset_type=${encodeURIComponent(assetType)}`,
      { method: 'GET' }
    );
  },
};

export type MediaUploadPurpose =
  | 'lecture_video'
  | 'lecture_note'
  | 'submission_attachment';

export interface MediaUploadInitRequest {
  purpose: MediaUploadPurpose;
  target_id: string;
  file_name: string;
  declared_size_bytes: number;
  declared_mime_type: string;
  extra_metadata?: Record<string, any>;
}

export interface MediaUploadInitResponse {
  upload_id: string;
  upload_url: string;
  object_key: string;
  bucket_name: string;
  expires_in_seconds: number;
  headers: Record<string, string>;
}

export interface MediaUploadCompleteResponse {
  upload_id: string;
  status: 'READY' | 'REJECTED' | 'PENDING' | 'VALIDATING';
  purpose: MediaUploadPurpose;
  target_id: string;
  object_key: string;
  actual_size_bytes: number;
  detected_mime_type: string;
  validated_at: string;
}

export interface MediaPlaybackResponse {
  playback_url: string;
  expires_in_seconds: number;
  mime_type: string | null;
  title: string;
  duration_seconds: number;
}

export interface MediaDownloadResponse {
  download_url: string;
  expires_in_seconds: number;
  file_name: string;
  file_size_bytes?: number;
}

export interface NoteItem {
  id: string;
  title: string;
  file_size_bytes: number;
  allow_download: boolean;
}

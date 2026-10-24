import React, { useState } from 'react';
import { mediaService } from '../../api/mediaService';
import type { MediaUploadPurpose, MediaUploadCompleteResponse } from '../../types/media';

interface TeacherMediaManagerProps {
  defaultLectureId?: string;
  onClose?: () => void;
  onUploadSuccess?: (result: MediaUploadCompleteResponse) => void;
}

export const TeacherMediaManager: React.FC<TeacherMediaManagerProps> = ({
  defaultLectureId = '',
  onClose,
  onUploadSuccess,
}) => {
  const [lectureId, setLectureId] = useState<string>(defaultLectureId);
  const [purpose, setPurpose] = useState<MediaUploadPurpose>('lecture_video');
  const [noteTitle, setNoteTitle] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Upload lifecycle state
  const [uploadState, setUploadState] = useState<
    'idle' | 'initiating' | 'transferring' | 'validating' | 'ready' | 'error'
  >('idle');
  const [progressPercent, setProgressPercent] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [successResult, setSuccessResult] = useState<MediaUploadCompleteResponse | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setUploadState('idle');
      setErrorMessage('');
    }
  };

  const handleStartUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lectureId.trim()) {
      setErrorMessage('Please enter or select a valid Lecture ID');
      return;
    }
    if (!selectedFile) {
      setErrorMessage('Please select a media file to upload');
      return;
    }

    setErrorMessage('');
    setProgressPercent(0);

    try {
      // Step 1: Request pre-signed upload ticket
      setUploadState('initiating');
      const extraMetadata = purpose === 'lecture_note' ? { title: noteTitle || selectedFile.name } : {};

      const ticket = await mediaService.initiateUpload({
        purpose,
        target_id: lectureId.trim(),
        file_name: selectedFile.name,
        declared_size_bytes: selectedFile.size,
        declared_mime_type: selectedFile.type || (purpose === 'lecture_video' ? 'video/mp4' : 'application/pdf'),
        extra_metadata: extraMetadata,
      });

      // Step 2: Direct client-to-storage transfer with progress
      setUploadState('transferring');
      await mediaService.directUpload(
        ticket.upload_url,
        selectedFile,
        selectedFile.type || 'application/octet-stream',
        (pct) => setProgressPercent(pct)
      );

      // Step 3: Complete upload and trigger server-side validation
      setUploadState('validating');
      const completeRes = await mediaService.completeUpload(ticket.upload_id);

      // Step 4: Success!
      setSuccessResult(completeRes);
      setUploadState('ready');
      if (onUploadSuccess) {
        onUploadSuccess(completeRes);
      }
    } catch (err: any) {
      setUploadState('error');
      setErrorMessage(
        err.data?.error || err.message || 'Media upload failed. Please try again.'
      );
    }
  };

  return (
    <div className="bg-slate-800 rounded-2xl border border-slate-700/80 p-6 max-w-lg w-full text-slate-100 shadow-2xl">
      <div className="flex items-center justify-between pb-4 border-b border-slate-700/60">
        <div>
          <h2 className="text-lg font-bold text-white">Upload Course Media</h2>
          <p className="text-xs text-slate-400">Direct encrypted object storage transfer</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-700 transition-colors"
          >
            ✕
          </button>
        )}
      </div>

      {uploadState === 'ready' && successResult ? (
        <div className="py-6 text-center">
          <div className="w-12 h-12 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-3 text-xl">
            ✓
          </div>
          <h3 className="text-base font-semibold text-emerald-300">
            {successResult.purpose === 'lecture_video' ? 'Video Published Successfully' : 'Note Added Successfully'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Status: <span className="text-emerald-400 font-mono font-medium">{successResult.status}</span>
          </p>
          <p className="text-xs text-slate-400">
            Format: {successResult.detected_mime_type} • Size: {(successResult.actual_size_bytes / (1024 * 1024)).toFixed(2)} MB
          </p>
          <div className="mt-6 flex justify-center space-x-3">
            <button
              onClick={() => {
                setUploadState('idle');
                setSelectedFile(null);
                setSuccessResult(null);
              }}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-xs font-medium rounded-xl transition-colors"
            >
              Upload Another File
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-xl transition-colors"
              >
                Done
              </button>
            )}
          </div>
        </div>
      ) : (
        <form onSubmit={handleStartUpload} className="mt-4 space-y-4">
          {/* Target Lecture UUID */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Lecture ID (UUID)
            </label>
            <input
              type="text"
              value={lectureId}
              onChange={(e) => setLectureId(e.target.value)}
              placeholder="e.g. 593bd0f4-74aa-4c0a-8e3f-aad68b90aac1"
              required
              disabled={uploadState === 'transferring' || uploadState === 'validating'}
              className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          {/* Media Purpose Selection */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Media Type
            </label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => setPurpose('lecture_video')}
                disabled={uploadState === 'transferring' || uploadState === 'validating'}
                className={`py-2 px-3 rounded-xl border text-xs font-medium flex items-center justify-center space-x-2 transition-all ${
                  purpose === 'lecture_video'
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                <span>🎥 Lecture Video</span>
              </button>
              <button
                type="button"
                onClick={() => setPurpose('lecture_note')}
                disabled={uploadState === 'transferring' || uploadState === 'validating'}
                className={`py-2 px-3 rounded-xl border text-xs font-medium flex items-center justify-center space-x-2 transition-all ${
                  purpose === 'lecture_note'
                    ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                    : 'bg-slate-900 border-slate-700 text-slate-400 hover:border-slate-600'
                }`}
              >
                <span>📄 PDF Notes</span>
              </button>
            </div>
          </div>

          {/* Optional Note Title */}
          {purpose === 'lecture_note' && (
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Note Title / Description
              </label>
              <input
                type="text"
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
                placeholder="e.g. Chapter 1 Formula Sheet"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          {/* File Picker */}
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">
              Select File ({purpose === 'lecture_video' ? 'MP4/WebM, up to 1.5GB' : 'PDF, up to 50MB'})
            </label>
            <input
              type="file"
              accept={purpose === 'lecture_video' ? 'video/mp4,video/webm' : 'application/pdf'}
              onChange={handleFileChange}
              disabled={uploadState === 'transferring' || uploadState === 'validating'}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-slate-700 file:text-slate-200 hover:file:bg-slate-600 cursor-pointer"
            />
          </div>

          {/* Progress / Status Display */}
          {(uploadState === 'transferring' || uploadState === 'validating') && (
            <div className="bg-slate-900/80 rounded-xl p-3 border border-slate-700/60">
              <div className="flex justify-between text-xs text-slate-300 mb-1.5 font-medium">
                <span>
                  {uploadState === 'transferring' ? 'Uploading directly to storage...' : 'Validating file signature...'}
                </span>
                <span>{uploadState === 'transferring' ? `${progressPercent}%` : 'Verifying'}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-500 h-2 rounded-full transition-all duration-200"
                  style={{ width: `${uploadState === 'validating' ? 100 : progressPercent}%` }}
                />
              </div>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="p-3 bg-rose-950/40 border border-rose-600/30 rounded-xl text-rose-300 text-xs">
              {errorMessage}
            </div>
          )}

          {/* Action Button */}
          <button
            type="submit"
            disabled={!selectedFile || uploadState === 'transferring' || uploadState === 'validating'}
            className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs rounded-xl shadow-lg shadow-indigo-600/20 transition-all cursor-pointer"
          >
            {uploadState === 'initiating'
              ? 'Requesting Upload Ticket...'
              : uploadState === 'transferring'
              ? 'Transferring Media...'
              : uploadState === 'validating'
              ? 'Validating File Content...'
              : 'Upload and Publish Media'}
          </button>
        </form>
      )}
    </div>
  );
};

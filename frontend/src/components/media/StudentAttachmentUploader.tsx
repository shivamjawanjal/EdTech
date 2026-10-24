import React, { useState } from 'react';
import { mediaService } from '../../api/mediaService';
import type { MediaUploadCompleteResponse } from '../../types/media';

interface StudentAttachmentUploaderProps {
  submissionId: string;
  pageOrder?: number;
  onSuccess?: (result: MediaUploadCompleteResponse) => void;
  onCancel?: () => void;
}

export const StudentAttachmentUploader: React.FC<StudentAttachmentUploaderProps> = ({
  submissionId,
  pageOrder = 1,
  onSuccess,
  onCancel,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<
    'idle' | 'initiating' | 'transferring' | 'validating' | 'done' | 'error'
  >('idle');
  const [progress, setProgress] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setStatus('idle');
      setErrorMessage('');
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setErrorMessage('Please select a photo or PDF to attach');
      return;
    }

    setErrorMessage('');
    setProgress(0);

    try {
      // 1. Scoped upload authorization
      setStatus('initiating');
      const ticket = await mediaService.initiateUpload({
        purpose: 'submission_attachment',
        target_id: submissionId,
        file_name: file.name,
        declared_size_bytes: file.size,
        declared_mime_type: file.type || 'image/jpeg',
        extra_metadata: { page_order: pageOrder },
      });

      // 2. Direct browser-to-storage transfer (no multi-megabyte payload through FastAPI)
      setStatus('transferring');
      await mediaService.directUpload(
        ticket.upload_url,
        file,
        file.type || 'image/jpeg',
        (pct) => setProgress(pct)
      );

      // 3. Complete and validate stored object
      setStatus('validating');
      const result = await mediaService.completeUpload(ticket.upload_id);

      setStatus('done');
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err: any) {
      setStatus('error');
      setErrorMessage(
        err.data?.error || err.message || 'Attachment upload failed. Please try again.'
      );
    }
  };

  return (
    <div className="bg-slate-800 rounded-2xl border border-slate-700 p-5 max-w-md w-full text-slate-100">
      <div className="flex items-center justify-between pb-3 border-b border-slate-700/60 mb-4">
        <div>
          <h3 className="text-sm font-bold text-white">Upload Homework Page {pageOrder}</h3>
          <p className="text-xs text-slate-400">Accepted: JPEG, PNG, WebP, PDF (max 15MB)</p>
        </div>
        {onCancel && (
          <button onClick={onCancel} className="text-slate-400 hover:text-white text-sm">
            ✕
          </button>
        )}
      </div>

      {status === 'done' ? (
        <div className="py-4 text-center">
          <div className="w-10 h-10 bg-emerald-500/10 text-emerald-400 rounded-full flex items-center justify-center mx-auto mb-2 text-lg">
            ✓
          </div>
          <p className="text-sm font-semibold text-emerald-300">Page Uploaded & Verified</p>
          <p className="text-xs text-slate-400 mt-1">Attachment safely linked to your submission</p>
        </div>
      ) : (
        <form onSubmit={handleUpload} className="space-y-4">
          <div>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,application/pdf"
              onChange={handleFileChange}
              disabled={status === 'transferring' || status === 'validating'}
              className="w-full text-xs text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-slate-700 file:text-slate-200 hover:file:bg-slate-600 cursor-pointer"
            />
          </div>

          {(status === 'transferring' || status === 'validating') && (
            <div className="bg-slate-900 rounded-xl p-3 border border-slate-700">
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>{status === 'transferring' ? 'Uploading file...' : 'Validating bytes...'}</span>
                <span>{status === 'transferring' ? `${progress}%` : 'Verifying'}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-emerald-500 h-1.5 rounded-full transition-all duration-150"
                  style={{ width: `${status === 'validating' ? 100 : progress}%` }}
                />
              </div>
            </div>
          )}

          {errorMessage && (
            <div className="p-2.5 bg-rose-950/40 border border-rose-600/30 rounded-xl text-rose-300 text-xs">
              {errorMessage}
            </div>
          )}

          <div className="flex items-center justify-end space-x-2 pt-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                disabled={status === 'transferring' || status === 'validating'}
                className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-medium rounded-lg"
              >
                Cancel
              </button>
            )}
            <button
              type="submit"
              disabled={!file || status === 'transferring' || status === 'validating'}
              className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium rounded-lg"
            >
              {status === 'initiating'
                ? 'Requesting URL...'
                : status === 'transferring'
                ? 'Uploading...'
                : status === 'validating'
                ? 'Verifying...'
                : 'Upload Attachment'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

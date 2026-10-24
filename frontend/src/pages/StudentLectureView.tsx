import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { mediaService } from '../api/mediaService';
import type { MediaPlaybackResponse } from '../types/media';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export const StudentLectureView: React.FC = () => {
  const { lectureId } = useParams<{ lectureId: string }>();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [playbackData, setPlaybackData] = useState<MediaPlaybackResponse | null>(null);
  const [errorStatus, setErrorStatus] = useState<
    'none' | 'unavailable' | 'expired' | 'forbidden' | 'error'
  >('none');
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [remainingTime, setRemainingTime] = useState<number>(0);
  const [downloadingNoteId, setDownloadingNoteId] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);

  const fetchPlaybackUrl = useCallback(async () => {
    if (!lectureId) return;
    setIsLoading(true);
    setErrorStatus('none');
    setErrorMessage('');

    try {
      const data = await mediaService.getPlaybackUrl(lectureId);
      setPlaybackData(data);
      setRemainingTime(data.expires_in_seconds);
    } catch (err: any) {
      if (err.status === 404) {
        setErrorStatus('unavailable');
        setErrorMessage(
          err.data?.error || 'Lecture video has not been published or uploaded yet.'
        );
      } else if (err.status === 403) {
        setErrorStatus('forbidden');
        setErrorMessage(
          err.data?.error || 'You are not enrolled in the course for this lecture.'
        );
      } else {
        setErrorStatus('error');
        setErrorMessage(err.data?.error || 'Failed to load video stream. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [lectureId]);

  useEffect(() => {
    fetchPlaybackUrl();
  }, [fetchPlaybackUrl]);

  // Expiration Countdown Timer
  useEffect(() => {
    if (remainingTime <= 0) return;
    const timer = setInterval(() => {
      setRemainingTime((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          setErrorStatus('expired');
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [remainingTime]);

  // Handle Video Element Playback Error
  const handleVideoError = () => {
    if (remainingTime === 0) {
      setErrorStatus('expired');
    }
  };

  const handleDownloadNote = async (noteId: string, title: string) => {
    try {
      setDownloadingNoteId(noteId);
      const res = await mediaService.getDownloadUrl(noteId, 'lecture_note');
      // Create temporary anchor to initiate browser download
      const link = document.createElement('a');
      link.href = res.download_url;
      link.download = res.file_name || `${title}.pdf`;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err: any) {
      alert(err.data?.error || 'Failed to generate download link. Please try again.');
    } finally {
      setDownloadingNoteId(null);
    }
  };

  const formatCountdown = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 pb-16">
      {/* Top Header */}
      <header className="sticky top-0 z-20 bg-slate-800/90 backdrop-blur border-b border-slate-700/60 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <button
            onClick={() => navigate('/student/home')}
            className="flex items-center space-x-2 text-slate-300 hover:text-white transition-colors"
          >
            <span className="text-lg">←</span>
            <span className="text-sm font-medium">Dashboard</span>
          </button>
          <div className="flex items-center space-x-3">
            <span className="text-xs text-slate-400">Secure Media Stream</span>
            {remainingTime > 0 && errorStatus === 'none' && (
              <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-xs px-2.5 py-1 rounded-full font-mono">
                Link expires in: {formatCountdown(remainingTime)}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 mt-6">
        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-24 bg-slate-800/40 rounded-2xl border border-slate-700/50">
            <LoadingSpinner size="lg" />
            <p className="mt-4 text-slate-400 text-sm">
              Authorizing access and fetching secure signed playback link...
            </p>
          </div>
        )}

        {/* Expired URL State */}
        {!isLoading && errorStatus === 'expired' && (
          <div className="bg-amber-950/40 border border-amber-600/40 rounded-2xl p-8 text-center my-8">
            <div className="w-12 h-12 bg-amber-500/10 text-amber-400 rounded-full flex items-center justify-center mx-auto mb-4 text-xl">
              ⏱
            </div>
            <h2 className="text-xl font-semibold text-amber-200">Playback Link Expired</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-md mx-auto">
              Media URLs are short-lived (30 minutes) to safeguard proprietary course content.
              Your watch session has ended.
            </p>
            <button
              onClick={fetchPlaybackUrl}
              className="mt-6 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl shadow-lg shadow-indigo-600/30 transition-all cursor-pointer"
            >
              Refresh Stream Link
            </button>
          </div>
        )}

        {/* Unavailable Media State */}
        {!isLoading && errorStatus === 'unavailable' && (
          <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-10 text-center my-8">
            <div className="w-14 h-14 bg-indigo-500/10 text-indigo-400 rounded-2xl flex items-center justify-center mx-auto mb-4 text-2xl">
              🎬
            </div>
            <h2 className="text-xl font-semibold text-white">Video Not Ready Yet</h2>
            <p className="mt-2 text-sm text-slate-400 max-w-md mx-auto">
              {errorMessage || 'Your instructor is preparing this lecture recording. Please check back shortly.'}
            </p>
            <Link
              to="/student/home"
              className="mt-6 inline-block px-5 py-2.5 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl transition-all"
            >
              Back to Course Home
            </Link>
          </div>
        )}

        {/* Forbidden / Access Denied */}
        {!isLoading && errorStatus === 'forbidden' && (
          <div className="bg-rose-950/40 border border-rose-600/40 rounded-2xl p-8 text-center my-8">
            <div className="w-12 h-12 bg-rose-500/10 text-rose-400 rounded-full flex items-center justify-center mx-auto mb-4 text-xl">
              🔒
            </div>
            <h2 className="text-xl font-semibold text-rose-200">Course Enrollment Required</h2>
            <p className="mt-2 text-sm text-slate-300 max-w-md mx-auto">{errorMessage}</p>
            <Link
              to="/student/home"
              className="mt-6 inline-block px-5 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-xl"
            >
              Return to Enrolled Courses
            </Link>
          </div>
        )}

        {/* General Error State */}
        {!isLoading && errorStatus === 'error' && (
          <div className="bg-slate-800/40 border border-rose-500/30 rounded-2xl p-8 text-center my-8">
            <p className="text-rose-400 text-sm mb-4">{errorMessage}</p>
            <button
              onClick={fetchPlaybackUrl}
              className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-xl"
            >
              Retry Loading Stream
            </button>
          </div>
        )}

        {/* Ready Video Stream State */}
        {!isLoading && errorStatus === 'none' && playbackData && (
          <div>
            {/* Video Player Container */}
            <div className="relative aspect-video w-full rounded-2xl overflow-hidden bg-black shadow-2xl border border-slate-700/60">
              <video
                ref={videoRef}
                src={playbackData.playback_url}
                controls
                playsInline
                autoPlay={false}
                onError={handleVideoError}
                className="w-full h-full object-contain"
                controlsList="nodownload"
              >
                Your browser does not support HTML5 video playback.
              </video>
            </div>

            {/* Video Details & Meta */}
            <div className="mt-6 flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800">
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight">
                  {playbackData.title}
                </h1>
                <p className="text-xs text-slate-400 mt-1 flex items-center space-x-2">
                  <span>Standard Class Stream</span>
                  <span>•</span>
                  <span>Direct Encrypted Delivery</span>
                </p>
              </div>

              {/* Player Link Refresh Action */}
              <div className="mt-4 md:mt-0 flex items-center space-x-3">
                <button
                  onClick={fetchPlaybackUrl}
                  title="Renew signed stream ticket"
                  className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium rounded-lg border border-slate-700 transition-colors"
                >
                  ↻ Refresh Link
                </button>
              </div>
            </div>

            {/* Downloadable Lecture Notes Section */}
            <section className="mt-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Lecture Notes & Materials</h2>
                <span className="text-xs text-slate-400">PDF downloads are access-controlled</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-slate-800/50 hover:bg-slate-800/80 border border-slate-700/50 rounded-xl p-4 flex items-center justify-between transition-colors">
                  <div className="flex items-center space-x-3 truncate mr-3">
                    <div className="w-9 h-9 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center font-bold text-xs shrink-0">
                      PDF
                    </div>
                    <div className="truncate">
                      <p className="text-sm font-medium text-slate-200 truncate">
                        Lecture Summary & Formulas
                      </p>
                      <p className="text-xs text-slate-400">Signed 15-minute download ticket</p>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownloadNote(lectureId || '', playbackData.title)}
                    disabled={downloadingNoteId !== null}
                    className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-xs font-medium rounded-lg transition-colors shrink-0 disabled:opacity-50"
                  >
                    {downloadingNoteId ? 'Generating...' : 'Download'}
                  </button>
                </div>
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  );
};

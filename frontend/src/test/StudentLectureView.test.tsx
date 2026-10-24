import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { StudentLectureView } from '../pages/StudentLectureView';
import { mediaService } from '../api/mediaService';
import { ApiError } from '../api/client';

vi.mock('../api/mediaService', () => ({
  mediaService: {
    getPlaybackUrl: vi.fn(),
    getDownloadUrl: vi.fn(),
  },
}));

describe('StudentLectureView Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderComponent = (lectureId = 'lecture-123') => {
    return render(
      <MemoryRouter initialEntries={[`/student/lectures/${lectureId}`]}>
        <Routes>
          <Route path="/student/lectures/:lectureId" element={<StudentLectureView />} />
          <Route path="/student/home" element={<div>Student Home</div>} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders loading spinner while requesting signed playback URL', () => {
    vi.mocked(mediaService.getPlaybackUrl).mockImplementation(
      () => new Promise(() => {}) // never resolves to inspect loading
    );

    renderComponent();
    expect(screen.getByText(/Authorizing access and fetching secure signed playback link/i)).toBeInTheDocument();
  });

  it('renders HTML5 video player and lecture title upon authorization success', async () => {
    vi.mocked(mediaService.getPlaybackUrl).mockResolvedValueOnce({
      playback_url: 'https://mock-storage.edtech.local/edtech-media-dev/lectures/123/video.mp4?sig=abc',
      expires_in_seconds: 1800,
      mime_type: 'video/mp4',
      title: 'Chapter 1: Trigonometric Identities',
      duration_seconds: 2400,
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Chapter 1: Trigonometric Identities')).toBeInTheDocument();
    });

    const video = document.querySelector('video');
    expect(video).toBeInTheDocument();
    expect(video?.getAttribute('src')).toContain('mock-storage.edtech.local');
    expect(screen.getByText(/Link expires in:/i)).toBeInTheDocument();
  });

  it('renders unavailable media message when video has not been uploaded (404)', async () => {
    vi.mocked(mediaService.getPlaybackUrl).mockRejectedValueOnce(
      new ApiError(404, { error: 'Lecture video has not been uploaded yet' })
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Video Not Ready Yet')).toBeInTheDocument();
    });
    expect(screen.getByText(/Lecture video has not been uploaded yet/i)).toBeInTheDocument();
    expect(screen.getByText(/Back to Course Home/i)).toBeInTheDocument();
  });

  it('renders enrollment required message when student is not enrolled (403)', async () => {
    vi.mocked(mediaService.getPlaybackUrl).mockRejectedValueOnce(
      new ApiError(403, { error: 'You are not enrolled in the course for this lecture' })
    );

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Course Enrollment Required')).toBeInTheDocument();
    });
    expect(screen.getByText(/You are not enrolled in the course for this lecture/i)).toBeInTheDocument();
  });

  it('triggers notes download when download button is clicked', async () => {
    vi.mocked(mediaService.getPlaybackUrl).mockResolvedValueOnce({
      playback_url: 'https://mock-storage.edtech.local/stream.mp4',
      expires_in_seconds: 1800,
      mime_type: 'video/mp4',
      title: 'Heights & Distances',
      duration_seconds: 1200,
    });

    vi.mocked(mediaService.getDownloadUrl).mockResolvedValueOnce({
      download_url: 'https://mock-storage.edtech.local/notes/notes.pdf?sig=def',
      expires_in_seconds: 900,
      file_name: 'Heights_Formula.pdf',
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Heights & Distances')).toBeInTheDocument();
    });

    const downloadBtn = screen.getByRole('button', { name: /Download/i });
    fireEvent.click(downloadBtn);

    await waitFor(() => {
      expect(mediaService.getDownloadUrl).toHaveBeenCalledWith('lecture-123', 'lecture_note');
    });
  });
});

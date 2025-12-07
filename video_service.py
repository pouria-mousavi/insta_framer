import cv2
import os
import numpy as np

class VideoService:
    def get_blur_score(self, image):
        """
        Calculates sharpness score using Laplacian Variance.
        Implements center-weighting to favor subject focus.
        """
        if image is None: 
            return 0.0
            
        # 1. Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 2. Apply slight Gaussian Blur to reduce noise (grain) which mimics sharpness
        # This helps ignore high-ISO noise in dark videos
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 3. Calculate Global Score (Whole Frame)
        global_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 4. Calculate Center Score (Subject Focus)
        h, w = gray.shape
        center_h, center_w = h // 2, w // 2
        crop_h, crop_w = h // 2, w // 2 # 50% crop
        
        start_y = center_h - (crop_h // 2)
        start_x = center_w - (crop_w // 2)
        
        center_crop = gray[start_y:start_y+crop_h, start_x:start_x+crop_w]
        center_score = cv2.Laplacian(center_crop, cv2.CV_64F).var()
        
        # 5. Calculate Weighted Score
        # Problem: If we use max(), a sharp background (static) always wins even if the subject (center) is blurry.
        # Solution: Use Weighted Average. 
        # heavily weight the center (subject) so that if they are blurry, the score drops.
        # 70% Center, 30% Global.
        final_score = (0.7 * center_score) + (0.3 * global_score)
        
        return final_score

    def analyze_video(self, video_path, min_distance=15):
        """
        Analyzes the video and returns a list of candidate frames sorted by sharpness score.
        Returns: list of (frame_index, score)
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []

        all_scored_frames = []
        frame_count = 0

        while True:
            success, frame = cap.read()
            if not success:
                break
            
            score = self.get_blur_score(frame)
            
            # Keep everything that isn't completely black/blank (threshold > 10)
            if score > 10.0:
                all_scored_frames.append((frame_count, score))
            
            frame_count += 1
        
        cap.release()

        # Sort by score descending to find best frames
        all_scored_frames.sort(key=lambda x: x[1], reverse=True)
        
        # Filter for diversity (time distance)
        final_candidates = []
        
        for frame_idx, score in all_scored_frames:
            # Check distance against ALREADY selected high-score frames
            too_close = False
            for existing_idx, _ in final_candidates:
                if abs(frame_idx - existing_idx) < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                final_candidates.append((frame_idx, score))
        
        # Return ALL candidates sorted by score (best first)
        # We don't sort by time here because we want to present the *best* options first, 
        # or we sort by time for the specific page being viewed.
        # Actually, user viewing "best" frames might prefer time-ordered for context.
        # But for pagination, we grab Top N best, then Sort those N by time.
        return final_candidates

    def save_frames(self, video_path, candidates, output_dir):
        """
        Saves specific frame indices from the video.
        candidates: list of (frame_idx, score)
        
        Returns: list of (filepath, score) sorted by frame_index (time)
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # candidates might be sorted by score. 
        # We want to save them and name them sequentially or by frame?
        # User sees "1, 2, 3". 
        # We should sort by time so "1" is start of video and "10" is end.
        candidates_sorted_by_time = sorted(candidates, key=lambda x: x[0])
        
        saved_frames = []
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return []
            
        for i, (frame_idx, score) in enumerate(candidates_sorted_by_time):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            success, frame = cap.read()
            if success:
                # Use frame_idx in filename to ensure uniqueness across pages if needed,
                # or just use a counter if we are generating a fresh batch.
                filename = f"frame_{frame_idx}.jpg" 
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, frame)
                saved_frames.append((filepath, score))
                
        cap.release()
        return saved_frames


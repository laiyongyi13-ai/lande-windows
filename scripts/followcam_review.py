"""Analyze handheld full-court footage and export clips for review."""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from itertools import pairwise
from pathlib import Path

import cv2
from scan_video import open_video, scan_video
from basketball_highlight.events import find_candidate_crossings
from basketball_highlight.inference import load_detector, select_device


MERGE_GAP_SECONDS = 15
NEARBY_REVIEW_SECONDS = 15
PERSISTENT_HOOP_SECONDS = 6


def hoop_tracks(records):
    tracks = []
    for record in records:
        time = record["time"]
        boxes = [d["xyxy"] for d in record["detections"]
                 if d["name"] == "hoop" and d["confidence"] >= 0.35]
        matches = []
        for track_id, track in enumerate(tracks):
            last_time, previous = track[-1]
            gap = time - last_time
            if gap > 1.05:
                continue
            for index, box in enumerate(boxes):
                width = previous[2] - previous[0]
                ratio = (box[2] - box[0]) / max(width, 1)
                distance = sum(abs(a - b) for a, b in zip(box, previous)) / 4
                # Bridge one missing sample only when the hoop has barely moved.
                if gap > 0.76:
                    acceptable = 0.8 <= ratio <= 1.25 and distance <= max(5, width * 0.3)
                else:
                    acceptable = 0.55 <= ratio <= 1.8 and distance <= max(24, width * 1.8)
                if acceptable:
                    matches.append((distance, track_id, index))
        used_tracks, used_boxes = set(), set()
        for _, track_id, index in sorted(matches):
            if track_id not in used_tracks and index not in used_boxes:
                tracks[track_id].append((time, boxes[index]))
                used_tracks.add(track_id)
                used_boxes.add(index)
        tracks.extend([(time, box)] for index, box in enumerate(boxes)
                      if index not in used_boxes)
    return [track for track in tracks if len(track) >= 2]


def sample_schedule(tracks, fps, sample_fps, windows=None):
    schedule = defaultdict(list)
    for track_id, track in enumerate(tracks):
        intervals = windows.get(track_id, []) if windows is not None else None
        if intervals == []:
            continue
        for (start, first), (end, last) in pairwise(track):
            for sample in range(round(start * sample_fps), round(end * sample_fps)):
                time = sample / sample_fps
                if intervals is not None and not any(a <= time <= b for a, b in intervals):
                    continue
                fraction = min(1.0, max(0.0, (time - start) / (end - start)))
                box = [a + (b - a) * fraction for a, b in zip(first, last)]
                schedule[round(time * fps)].append((track_id, box))
    return schedule


def detect_near_hoops(video, tracks, detector, device, sample_fps, windows=None):
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open {video}")
    fps = cap.get(cv2.CAP_PROP_FPS)
    schedule = sample_schedule(tracks, fps, fps if windows is not None else sample_fps, windows)
    records = defaultdict(list)
    crops, metadata = [], []

    def flush():
        if not crops:
            return
        results = detector.predict(crops, device=device, conf=0.2, imgsz=416 if windows is not None else 320, verbose=False)
        for result, (track_id, frame, box, left, top) in zip(results, metadata, strict=True):
            x1, y1, x2, y2 = box
            width = x2 - x1
            rim_x = (x1 + x2) / 2
            rim_y = (y1 + y2) / 2 - (y2 - y1) * 0.28
            normalized, actual = [], []
            for det in result.boxes:
                if result.names[int(det.cls.item())] != "ball":
                    continue
                a, b, c, d = det.xyxy[0].tolist()
                actual.append([a + left, b + top, c + left, d + top])
                xyxy = [(a + left - rim_x) * 50 / width, (b + top - rim_y) * 50 / width,
                        (c + left - rim_x) * 50 / width, (d + top - rim_y) * 50 / width]
                normalized.append({"name": "ball", "confidence": det.conf.item(),
                                   "xyxy": xyxy,
                                   "center": [(xyxy[0] + xyxy[2]) / 2, (xyxy[1] + xyxy[3]) / 2]})
            records[track_id].append({"time": frame / fps, "detections": normalized,
                                      "hoop_box": box, "ball_boxes": actual})
        crops.clear()
        metadata.clear()

    try:
        for frame in range(max(schedule, default=-1) + 1):
            if not cap.grab():
                break
            if frame not in schedule:
                continue
            ok, image = cap.retrieve()
            if not ok:
                break
            height, image_width = image.shape[:2]
            for track_id, box in schedule[frame]:
                x1, y1, x2, y2 = box
                pad = max(24, x2 - x1)
                left, top = max(0, int(x1 - 2 * pad)), max(0, int(y1 - 3 * pad))
                crop = image[top:min(height, int(y2 + 2 * pad)),
                             left:min(image_width, int(x2 + 2 * pad))]
                if crop.size:
                    crops.append(crop)
                    metadata.append((track_id, frame, box, left, top))
                if len(crops) >= 16:
                    flush()
        flush()
    finally:
        cap.release()
    return records


def approach_times(samples):
    """Find observed descending approaches that may be occluded at the rim."""
    previous = []
    previous_time = 0
    approaches = []
    for sample in samples:
        time = sample["time"]
        points = [d["center"] for d in sample["detections"]]
        gap = time - previous_time
        if 0 < gap <= 0.3:
            for x, y in points:
                if not (-27 <= y <= 0 and abs(x) <= 30):
                    continue
                for old_x, old_y in previous:
                    descent = y - old_y
                    if 6 <= descent <= 65 and abs(x - old_x) <= 36:
                        projected_x = x - y * (x - old_x) / descent
                        if abs(projected_x) <= 27:
                            approaches.append(time)
                            break
        previous, previous_time = points, time
    return approaches


def review_events(records, dense_records):
    rim = {"center_x": 0, "rim_y": 0, "width": 50}
    candidates = []
    for track_id, samples in records.items():
        dense = dense_records.get(track_id, [])
        confirmed = find_candidate_crossings(dense, rim, max_gap_sec=0.35, margin=5)
        coarse = find_candidate_crossings(samples, rim, max_gap_sec=0.35, margin=5)
        for evidence, events in (
            ("dense_crossing", confirmed),
            ("coarse_crossing", coarse),
            ("occluded_or_incomplete", [{"time": time} for time in approach_times(samples)]),
        ):
            for event in events:
                if any(other["hoop_track"] == track_id and abs(event["time"] - other["time"]) <= 0.8
                       for other in candidates):
                    continue
                candidates.append(dict(event, hoop_track=track_id, evidence=evidence))
    return sorted(candidates, key=lambda item: item["time"])


def group_candidates(candidates):
    groups = []
    for candidate in candidates:
        if not groups or candidate["time"] - groups[-1][-1]["time"] > MERGE_GAP_SECONDS:
            groups.append([])
        groups[-1].append(candidate)
    return groups


def review_windows(tracks, seed_events):
    windows = defaultdict(list)
    # Review persistent hoops even if coarse ball detection found no seed.
    for track_id, track in enumerate(tracks):
        start, end = track[0][0], track[-1][0]
        if end - start >= PERSISTENT_HOOP_SECONDS:
            windows[track_id].append((start, end))
    persistent_ids = set(windows)
    for event in seed_events:
        track_id = event["hoop_track"]
        if track_id not in persistent_ids:
            time = event["time"]
            windows[track_id].append((time - NEARBY_REVIEW_SECONDS, time + NEARBY_REVIEW_SECONDS))
    return windows


def render_clip(video, output, events, records):
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    start = max(0, round((events[0] - 4) * fps))
    stop = round((events[-1] + 3) * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start)
    writer = cv2.VideoWriter(str(output), cv2.VideoWriter_fourcc(*"mp4v"), fps,
                             (int(cap.get(3)), int(cap.get(4))))
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot write {output}")
    index = 0
    try:
        for frame in range(start, stop):
            ok, image = cap.read()
            if not ok:
                break
            time = frame / fps
            while index + 1 < len(records) and abs(records[index + 1]["time"] - time) < abs(records[index]["time"] - time):
                index += 1
            record = records[index]
            if abs(record["time"] - time) <= 0.10:
                for box, color in [(record["hoop_box"], (0, 220, 255)),
                                   *((box, (0, 255, 0)) for box in record["ball_boxes"])]:
                    x1, y1, x2, y2 = map(round, box)
                    cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            event = min(events, key=lambda candidate_time: abs(candidate_time - time))
            cv2.putText(image, f"Source {time:.2f}s | Candidate {event:.2f}s",
                        (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            writer.write(image)
    finally:
        cap.release()
        writer.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--detections", type=Path)
    inputs.add_argument("--video", type=Path)
    parser.add_argument("--model", type=Path, default=Path("models/bball_model.pt"))
    parser.add_argument("--candidates-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample-fps", type=int, default=8, choices=range(6, 13))
    args = parser.parse_args()
    if args.video is not None:
        cap = open_video(args.video)
        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if not cap.isOpened() or min(width, height) <= 0:
                parser.error(f"Cannot open video: {args.video}")
        finally:
            cap.release()
        # A unique run directory prevents accidental reuse of old detections.
        args.output.mkdir(parents=True, exist_ok=True)
        run = args.output / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        run.mkdir()
        args.output = run
        args.detections = run / "full-frame-detections.json"
        print(f"run_directory={run}", flush=True)
        print("stage=scan", flush=True)
        scan_video(argparse.Namespace(
            video=args.video.resolve(), model=args.model.resolve(), roi=[0, 0, width, height],
            scale=1, sample_fps=2, batch=8, conf=0.15, device="cpu",
            duration=None, time_offset=0, cache_dir=None, output=args.detections,
        ))
    data = json.loads(args.detections.read_text(encoding="utf-8"))
    print("stage=tracking", flush=True)
    if data["roi"][:2] != [0, 0] or data["effective_scale"] != 1:
        parser.error("Use unscaled full-frame detections from scan_video.py")
    video = Path(data["video"])
    tracks = hoop_tracks(data["records"])
    print(f"{video.name}: {len(tracks)} hoop tracks", flush=True)
    device = select_device("cpu")
    detector = load_detector(data["model"])
    records = detect_near_hoops(video, tracks, detector, device, args.sample_fps)
    windows = review_windows(tracks, review_events(records, {}))
    print(f"{sum(map(len, windows.values()))} windows for source-rate review", flush=True)
    print("stage=review", flush=True)
    dense = detect_near_hoops(video, tracks, detector, device, args.sample_fps, windows)
    candidates = review_events(records, dense)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.candidates_only:
        (args.output / "candidates.json").write_text(
            json.dumps({"candidates": candidates}, ensure_ascii=False), encoding="utf-8")
        return
    print("stage=export", flush=True)
    groups = group_candidates(candidates)
    for index, group in enumerate(groups, 1):
        times = [item["time"] for item in group]
        label = f"{times[0]:07.2f}s"
        if len(times) > 1:
            label += f"-{times[-1]:07.2f}s"
        clip = f"{index:03d}_{label}.mp4"
        for item in group:
            item["clip"] = clip
        track_ids = {item["hoop_track"] for item in group}
        overlay = sorted(
            (record for track_id in track_ids
             for record in records[track_id] + dense.get(track_id, [])),
            key=lambda record: record["time"],
        )
        render_clip(video, args.output / clip, times, overlay)
    (args.output / "candidates.json").write_text(
        json.dumps({"video": str(video), "track_count": len(tracks), "status": "review",
                    "candidates": candidates}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(candidates)} review candidates in {len(groups)} clips: {args.output}", flush=True)


if __name__ == "__main__":
    main()

"""Test script for processing a video and saving the output scores."""
import json

from app.services.video_pipeline import process_video

if __name__ == "__main__":
    video_path = "app/services/video_012.mp4"
    output_json_path = "app/services/output_scores.json"

    print(f"Starting processing for video: {video_path}\n")
    scores_json_list = process_video(video_path, stride=10, iou_threshold=0.5, question_amount=4)
    print(f"A total of {len(scores_json_list['scores'])} booklet(s) processed.\n")

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(scores_json_list, f, indent=2, ensure_ascii=False)

        print(f"\nScores saved to: {output_json_path}")

    except IOError as e:
        print(f"\nError while saving scores: {e}")

    good_results = [r for r in scores_json_list['scores'] if "error" not in r]
    bad_results = [r for r in scores_json_list['scores'] if "error" in r]

    print(f"\n--- Processing Summary ---")
    print(f"Total frames processed: {len(scores_json_list['scores'])}")
    print(f"Successful booklets: {len(good_results)}")
    print(f"Rejected frames (error): {len(bad_results)}")

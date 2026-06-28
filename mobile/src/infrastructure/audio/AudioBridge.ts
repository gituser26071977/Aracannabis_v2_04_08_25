/**
 * Audio — interface only.
 *
 * Implementation: react-native-track-player or native bridge.
 */

export type AudioCategory = 'ambient' | 'voice' | 'effect';

export interface AudioTrackRef {
  readonly id: string;
  readonly category: AudioCategory;
  readonly url: string;
  readonly loop: boolean;
  readonly volume: number; // 0..1
}

export interface AudioBridge {
  load(track: AudioTrackRef): Promise<void>;
  play(id: string): Promise<void>;
  pause(id: string): Promise<void>;
  stop(id: string): Promise<void>;
  setVolume(id: string, volume: number): Promise<void>;
  preload(tracks: readonly AudioTrackRef[]): Promise<void>;
  unloadAll(): Promise<void>;
}

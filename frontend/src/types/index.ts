export interface Artist {
  id: number;
  name: string;
  image_key?: string;
  tracks?: Track[]; 
  albums?: Album[];
}

export interface Album {
  id: number;
  name: string;
  image_key?: string;
  artist_id: number;
  artist?: Artist;
  tracks?: Track[];
}

export interface Track {
  id: number;
  title: string;
  image_key?: string;
  duration_seconds: number;
  genre: string[];
  artist?: Artist;
  album?: Album;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
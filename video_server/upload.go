package main

import (
  "log"
  "os"
  "strings"
  "google.golang.org/api/youtube/v3"
  "errors"
)

type metadata struct {
  Title string
  Description string
  Keywords string
  ID string
  ReturnURL string
}

func upload(filename string, data metadata) (string, error) {
  if filename == "" {
    return "", errors.New("You must provide a filename of a video file to upload")
  }

  client, err := buildOAuthHTTPClient(youtube.YoutubeUploadScope)
  if err != nil {
    log.Panicf("Error building OAuth client: %v", err)
  }

  service, err := youtube.New(client)
  if err != nil {
    log.Panicf("Error creating YouTube client: %v", err)
  }

  upload := &youtube.Video{
    Snippet: &youtube.VideoSnippet{
      Title:       data.Title,
      Description: data.Description,
      CategoryId:  "20",
    },
    Status: &youtube.VideoStatus{PrivacyStatus: "unlisted"},
  }

  // The API returns a 400 Bad Request response if tags is an empty string.
  if strings.Trim(data.Keywords, "") != "" {
    upload.Snippet.Tags = strings.Split(data.Keywords, ",")
  }

  call := service.Videos.Insert("snippet,status", upload)

  file, err := os.Open(filename)
  defer file.Close()
  if err != nil {
    log.Panicf("Error opening %v: %v", filename, err)
  }

  Info.Printf("Starting Upload of %v\n", filename)
  response, err := call.Media(file).Do()
  if err != nil {
    log.Panicf("Error making YouTube API call: %v", err)
  }
  Info.Printf("Upload successful! Video ID: %v\n", response.Id)
  return response.Id, nil
}

package main

import (
  "io"
  "net/http"
  "net/url"
  "os"
  "time"
  "github.com/golang/groupcache/lru"
  "strings"
  "github.com/kz26/m3u8"
  "encoding/json"
)

var USER_AGENT string

var client = &http.Client{}

func doRequest(c *http.Client, req *http.Request) (*http.Response, error) {
  req.Header.Set("User-Agent", USER_AGENT)
  resp, err := c.Do(req)
  return resp, err
}

type accessToken struct {
  Token string `json:"token"`
  Sig string `json:"sig"`
}

type Download struct {
  URI string
  totalDuration time.Duration
}

func getAccessToken(user string) (token accessToken) {
  req, _ := http.NewRequest("GET", "https://api.twitch.tv/api/channels/" + user + "/access_token", nil)
  req.Header.Set("Client-ID", "jzkbprff40iqj646a697cyrvl0zt2m6")
  r, err := client.Do(req)
  panicOnError(err)
  defer r.Body.Close()
  json.NewDecoder(r.Body).Decode(&token)
  Info.Println(token.Token)
  return
}

func record(filename string, url string, finish chan bool, data metadata) {
  msChan := make(chan *Download, 1024)
	go getStreamVideos(url, 0, msChan, finish)
	downloadSegment(filename, msChan, 0)
  id, err := upload(filename, data)
  panicOnError(err)
  notifyTournament(data.ReturnURL, data.ID, id)
  keepOnlyLast(3, "videos")
}

func getStream(user string) string {
  token := getAccessToken(user)
  urlBase := "http://usher.twitch.tv/api/channel/hls/" + user + ".m3u8"
  urlParams := "?player=twitchweb&token=" + token.Token + "&sig=" + token.Sig
  url := urlBase + urlParams
  req, err := http.NewRequest("GET", url, nil)
  panicOnError(err)
  resp, err := doRequest(client, req)
  panicOnError(err)
  playlist, listType, err := m3u8.DecodeFrom(resp.Body, true)
  panicOnError(err)
  resp.Body.Close()
  if listType != m3u8.MASTER {
    Error.Panicln("Should be a master m3u8 playlist.")
  }
  mpl := playlist.(*m3u8.MasterPlaylist)
  for _, x := range mpl.Variants {
    if x.VariantParams.Video == "720p60" {
      return x.URI
    }
  }
  for _, x := range mpl.Variants {
    if x.VariantParams.Video == "720p30" {
      return x.URI
    }
  }
  for _, x := range mpl.Variants {
    if x.VariantParams.Video == "480p30" {
      return x.URI
    }
  }
  return ""
}

func downloadSegment(fn string, dlc chan *Download, recTime time.Duration) {
  out, err := os.Create(fn)
  if err != nil {
    Error.Panicln(err)
  }
  defer out.Close()
  for v := range dlc {
    req, err := http.NewRequest("GET", v.URI, nil)
    panicOnError(err)
    resp, err := doRequest(client, req)
    if err != nil {
      Warn.Println(err)
      continue
    }
    if resp.StatusCode != 200 {
      Warn.Printf("Received HTTP %v for %v\n", resp.StatusCode, v.URI)
      continue
    }
    _, err = io.Copy(out, resp.Body)
    panicOnError(err)
    resp.Body.Close()
    if recTime != 0 {
      Info.Printf("Recorded %v of %v\n", v.totalDuration, recTime)
    } else {
      Info.Printf("Recorded %v\n", v.totalDuration)
    }
  }
  Info.Println("Done Recording.")
}

func getPlaylist(urlStr string) (m3u8.Playlist, m3u8.ListType) {
  req, err := http.NewRequest("GET", urlStr, nil)
  panicOnError(err)
  resp, err := doRequest(client, req)
  panicOnError(err)
  playlist, listType, err := m3u8.DecodeFrom(resp.Body, true)
  panicOnError(err)
  resp.Body.Close()
  return playlist, listType
}

func getStreamVideos(urlStr string, recTime time.Duration, dlc chan *Download, finish chan bool) {
  var recDuration time.Duration
  cache := lru.New(1024)
  playlistURL, err := url.Parse(urlStr)
  defer close(dlc)
  panicOnError(err)
  for {
    playlist, listType := getPlaylist(urlStr)
    if listType == m3u8.MEDIA {
      mpl := playlist.(*m3u8.MediaPlaylist)
      for _, v := range mpl.Segments {
        if v != nil {
          var msURI string
          if strings.HasPrefix(v.URI, "http") {
            msURI, err = url.QueryUnescape(v.URI)
            panicOnError(err)
          } else {
            msURL, err := playlistURL.Parse(v.URI)
            if err != nil {
              Warn.Println(err)
              continue
            }
            msURI, err = url.QueryUnescape(msURL.String())
            panicOnError(err)
          }
          _, hit := cache.Get(msURI)
          if !hit {
            cache.Add(msURI, nil)
            recDuration += time.Duration(int64(v.Duration * 1000000000))
            select {
              case <-finish:
                return
              default:
                dlc <- &Download{msURI, recDuration}
            }
          }
          if recTime != 0 && recDuration != 0 && recDuration >= recTime {
            return
          }
        }
      }
      if mpl.Closed {
          return
      } else {
        time.Sleep(time.Duration(int64(mpl.TargetDuration * 1000000000)))
      }
    } else {
      Error.Panicln("Not a valid media playlist")
    }
  }
}

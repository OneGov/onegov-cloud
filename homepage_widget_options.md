# Homepage Widgets
This is a description of the available homepage widgets and their corresponding options.


## Columns and Rows
```
<row-wide bgcolor="primary">
    <column span="12">
        <row>
            <column span="12">
                <title>Events</title>
                <events />
            </column>
        </row>
    </column>
</row-wide>
```
You can create different layouts with columns and rows. Columns and rows can contain other elements such as `<slider/>` for example.

### Rows
| Variable Name | Description                                | Value if left empty | Possible Values         |
| ------------- | ------------------------------------------ | ------------------- | ----------------------- |
| `bgcolor`     | The background color of the row            | -                   | primary, gray, darkgray |
| `class`       | Custom classes                             | -                   | Any class name          |

**Additional Info:**<br>
There are two different types of rows, `<row-wide> </row-wide>` and `<row> </row>`. `<row-wide> </row-wide>` streches over the whole screen while `<row> </row>` creates a container with the same width as the header and footer information.


### Columns
| Variable Name | Description                                | Value if left empty | Possible Values         |
| ------------- | ------------------------------------------ | ------------------- | ----------------------- |
| `span` | Each row is divided into 12 units. Columns can span over any number of these units. | 12 | 1 - 12 |
| `class`       | Custom classes                             | -                   | Any class name          |


## Slider

```
<slider
    height-m="30vw"
    height-d="55vh"
></slider>
```

| Variable Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `height-m`    | The height of the slider on mobile devices. Images will center themselves and cover the available space. | 40vw                | 30vw, 40vh, 100px, ... |
| `height-d`    | The height of the slider on desktop devices. Images will center themselves and cover the available space.| 40vw                | 30vw, 40vh, 100px, ... |
| `class`       | Custom classes                             | -                   | Any class name         |

### Additional Info:
The images for the slider are defined via photoalbums. You can find the "show on homepage"-Option in the settings of each album.

## Title
```
<title>
    Events
</title>
```
| Variable Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `class`       | Custom classes                             | -                   | Any class name         |

## Autoplay Video(s)
```
    <autoplay_video 
        max-height="100vh"
        text="Text on video"
        link_mp4="/storage/..."
        link_mp4_low_res="/storage/..."
        link_webm="/storage/..."
        link_webm_low_res="/storage/..."
    />
```
| Variable Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `max-height` | The *maximum* height of the video. Can for example be used for fullscreen videos on desktop. The video will center itself in the available space. | Video height                  | 30vw, 40vh, 100px, ... |
| `text`       | Text to be shown atop of the video | -                   | Any text         |
| `link_mp4_low_res`  | Link to the video in the mp4 format with reduced size uploaded in the files-section. Will be shown for mobile devices instead of the full sized video. | -                   | /storage/...         |
| `link_mp4`       | Link to the full sized video in the mp4 format uploaded in the files-section. Will be shown for desktop and mobile, if no smaller size is available. | -                   | /storage/...         |
| `class`       | Custom classes                             | -                   | Any class name         |
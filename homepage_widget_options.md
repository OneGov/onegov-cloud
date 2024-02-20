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
| Attribute Name | Description                                | Value if left empty | Possible Values         |
| ------------- | ------------------------------------------ | ------------------- | ----------------------- |
| `bgcolor`     | The background color of the row            | -                   | primary, gray, darkgray |
| `class`       | Custom classes                             | -                   | Any class name          |

#### Additional Info:
There are two different types of rows, `<row-wide> </row-wide>` and `<row> </row>`. `<row-wide> </row-wide>` streches over the whole screen while `<row> </row>` creates a container with the same width as the header and footer information.


### Columns
| Attribute Name | Description                                | Value if left empty | Possible Values         |
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

| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `height-m`    | The height of the slider on mobile devices. Images will center themselves and cover the available space. | 40vw                | 30vw, 40vh, 100px, ... |
| `height-d`    | The height of the slider on desktop devices. Images will center themselves and cover the available space.| 40vw                | 30vw, 40vh, 100px, ... |

#### Additional Info:
The images for the slider are defined via photoalbums. You can find the "show on homepage"-Option in the settings of each album.


## Title
```
<title>
    Events
</title>
```
| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `class`       | Custom classes                             | -                   | Any class name         |

## Text
```
<text>
    Some Text.
</text>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `class`       | Custom classes   | -                   | Any class name         |


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
| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `max-height` | The *maximum* height of the video. Can for example be used for fullscreen videos on desktop. The video will center itself in the available space. | Video height                  | 30vw, 40vh, 100px, ... |
| `text`       | Text to be shown atop of the video | -                   | Any text         |
| `link_mp4_low_res`  | Link to the video in the mp4 format with reduced size uploaded in the files-section. Will be shown for mobile devices instead of the full sized video. | -                   | /storage/...         |
| `link_mp4`       | Link to the full sized video in the mp4 format uploaded in the files-section. Will be shown for desktop and mobile, if no smaller size is available. | -                   | /storage/...         |
| `link_webm_low_res`  | Link to the video in the webm format with reduced size uploaded in the files-section. Will be shown for mobile devices instead of the full sized video. | -                   | /storage/...         |
| `link_webm`       | Link to the full sized video in the webm format uploaded in the files-section. Will be shown for desktop and mobile, if no smaller size is available. | -                   | /storage/...         |

#### Additional Info:
You can add multiple videos and wrap them with `<random_videos> </random_videos>` to display one of the videos at random each time the page gets refreshed. Like this:
```
<random_videos>
    <autoplay_video 
        link_mp4="/storage/video_1" />
    <autoplay_video 
        link_mp4="/storage/video_2" />

</random_videos>
```


## Icon Links
```
<icon_link 
    icon="fa-concierge-bell" 
    title="Online-Schalter"
    link="/forms"
    text="Nehmen Sie online bequem Dienstleistungen in Anspruch"
/>
```

| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `icon`       | Font Awesome icon class. You can choose any from the free icons of the Version 5 of Font Awesome here: [Font Awesome Icons](https://fontawesome.com/v5/search?o=r&m=free)   | **Cannot** be left empty * | fa-user, fa-building, fa-... |
| `title`       | Title of the icon link widget  | **Cannot** be left empty *     | Any text         |
| `text`       | Text of the icon link widget               | -         | Any text         |
| `text`       | Where the icon link widget is linked to     | -         | https://...         |
| `text`       | Inverts the colors of the icon link widget (white turns to primary color and vice versa).                 | false         | true, false         |
| `class`       | Custom classes                             | -                   | Any class name         |

\* Icon Link Widget will not be displayed if this value is missing


## Links
```
<links>
    <link url="/resources"
        description="Book now">
        Reservations
    </link>
    <link url="https://..."
        description="Something">
        Some Text
    </link>
</links>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `url`       | URL of the link   | -                   | https://...         |
| `description`  | Link Name   | -                   | Any text         |
| `class`       | Custom classes   | -                   | Any class name         |


## News
```
<news />
```
*No Attributes*

#### Additional Info:
You can adjust the number of displayed news items in the homepage-settings form.


## Events
```
<events />
```
*No Attributes*

#### Additional Info:
You can adjust the number of displayed events in the homepage-settings form.

## Partners
``` 
<partners />
```

| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `title`   | Custom title of section | Partners    | Any text         |
| `hide-title`   | Option to hide title, if the title attribute is empty the title will be "Partners". | false    | true, false         |

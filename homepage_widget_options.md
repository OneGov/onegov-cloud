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


## Title
[![Title](docs/_static/homepage_widgets//title.png?raw=true)]()
```
<title>
    Events
</title>
```
| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `class`       | Custom classes                             | -                   | Any class name         |


## Text
[![Text](docs/_static/homepage_widgets//text.png?raw=true)]()
```
<text>
    Some Text.
</text>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `class`       | Custom classes   | -                   | Any class name         |


## Slider
[![Slider](docs/_static/homepage_widgets//slider.png?raw=true)]()
```
<slider
    height-m="30vw"
    height-d="55vh"
    searchbox="true"
    searchbox-position="top"
></slider>
```

| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `height-m`    | The height of the slider on mobile devices. Images will center themselves and cover the available space. | 40vw                | 30vw, 40vh, 100px, ... |
| `height-d`    | The height of the slider on desktop devices. Images will center themselves and cover the available space.| 40vw                | 30vw, 40vh, 100px, ... |
| `searchbox`    | If there should be a searchbox in the slider.| false                | true, false |
| `searchbox-position`    | The position of the searchbox.| bottom                | top, bottom |

#### Additional Info:
The images for the slider are defined via photoalbums. You can find the "show on homepage"-Option in the settings of each album.


## Autoplay Video(s)
[![Autoplay Video](docs/_static/homepage_widgets//autoplay_video.png?raw=true)]()
```
<autoplay_video
    max-height="100vh"
    text="Text on video"
    button_url="https://..."
    button_text="Button Text"
    link_mp4="/storage/..."
    link_mp4_low_res="/storage/..."
    link_webm="/storage/..."
    link_webm_low_res="/storage/..."
    searchbox="true"
    searchbox-position="top"
/>
```
| Attribute Name | Description                                | Value if left empty | Possible Values        |
| ------------- | ------------------------------------------ | ------------------- | ---------------------- |
| `max-height` | The *maximum* height of the video. Can for example be used for fullscreen videos on desktop. The video will center itself in the available space. | Video height                  | 30vw, 40vh, 100px, ... |
| `text`       | Text to be shown atop of the video | -                   | Any text         |
| `button_url`       | Adds a button linked to the url | -                   | https://...         |
| `button_text`       | Text used as the label of the button. Button only appears if there is a button_url. | "Show more"                   | Any text         |
| `link_mp4_low_res`  | Link to the video in the mp4 format with reduced size uploaded in the files-section. Will be shown for mobile devices instead of the full sized video. | -                   | /storage/...         |
| `link_mp4`       | Link to the full sized video in the mp4 format uploaded in the files-section. Will be shown for desktop and mobile, if no smaller size is available. | -                   | /storage/...         |
| `link_webm_low_res`  | Link to the video in the webm format with reduced size uploaded in the files-section. Will be shown for mobile devices instead of the full sized video. | -                   | /storage/...         |
| `link_webm`       | Link to the full sized video in the webm format uploaded in the files-section. Will be shown for desktop and mobile, if no smaller size is available. | -                   | /storage/...         |
| `searchbox`    | If there should be a searchbox in the video.| false                | true, false |
| `searchbox-position`    | The position of the searchbox.| bottom                | top, bottom |

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
[![Icon Links](docs/_static/homepage_widgets//icon_links.png?raw=true)]()
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
| `invert`       | Inverts the colors of the icon link widget (white turns to primary color and vice versa).                 | false         | true, false         |
| `class`       | Custom classes                             | -                   | Any class name         |

\* Icon link widget will not be displayed if this value is missing


## Links
[![Links](docs/_static/homepage_widgets//links.png?raw=true)]()
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
[![News](docs/_static/homepage_widgets//news.png?raw=true)]()
```
<news />
```
*No Attributes*

#### Additional Info:
You can adjust the number of displayed news items in the homepage settings form.


## Events
[![Events](docs/_static/homepage_widgets//events.png?raw=true)]()
```
<events />
```
*No Attributes*

#### Additional Info:
You can adjust the number of displayed events in the homepage-settings form.

## Partners
[![Partners](docs/_static/homepage_widgets//partners.png?raw=true)]()
```
<partners />
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `title`   | Custom title of section | Partners    | Any text         |
| `hide-title`   | Option to hide title, if the title attribute is empty the title will be "Partners". | false    | true, false         |

#### Additional Info:
Partners can be edited in the footer settings.

## Services
[![Services](docs/_static/homepage_widgets//services.png?raw=true)]()
```
<panel>
    <services/>
</panel>
```
#### Additional Info:
The label and visibility of the services can be edited in the homepage settings. You can also add your own links to the services panel by using the links widget like this:
```
<panel>
    <services>
        <link url="/resources"
            description="Book now">
            Reservations
        </link>
    </services>
</panel>
```

## Contacts
[![Contacts](docs/_static/homepage_widgets/people.png?raw=true)]()
```
<contacts_and_albums/>
```

## Directories
[![Directories](docs/_static/homepage_widgets/directories.png?raw=true)]()
```
<directories/>
```

## Focus
[![Focus](docs/_static/homepage_widgets/focus.png?raw=true)]()
```
<focus
    image-src="https://..."
    focus-url="https://..."
    title="New Website"
    lead="We got a new website."
    text-on-image="True"
>
    <text>Lorem ipsum dolor sit amet, consetetur sadipscing elitr.</text>
    <text>Sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat.</text>
</focus>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `title`   | Custom title of focus widget, will be displayed on image if `text-on-image` is true.| -    | Any text         |
| `lead`   | Lead of focus widget, will be displayed on image if `text-on-image` is true. | -    | Any text         |
| `image-src`   | URL of the image for the focus card. | -    | https://...         |
| `focus-url`   | URL to which the focus card should link to. | -    | https://...         |
| `text-on-image` | If true `title` and `lead` are displayed atop of the image. | false | true, false |


## Testimonial
```
<testimonial
    image="https://..."
    description="Person name, job title"
    quote="I love my job very much, this place is greaet."
/>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `image`   | Image URL of the testimony.| -    | https://...
| `description` | Short description of who the person is (Name, job title, etc.).| -    | Any text
| `quote` | A quote of the person.| -    | Any text


## Testimonials Slider
[![Testimonials](docs/_static/homepage_widgets/testimonial_slider.png?raw=true)]()
```
<testimonial_slider
    image_1="https://..."
    description_1="Person name, job title"
    quote_1="I love my job very much, this place is greaet."

    image_2="https://..."
    description_2="Person name, political party"
    quote_2="Money is very important to me."

    image_3="https://..."
    description_3="Person name, teacher"
    quote_3="Children are our future."
/>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `image_1`   | Image URL of the #1 testimony.| -    | https://...
| `image_2`   | Image URL of the #2 testimony.| -    | https://...
| `image_3`   | Image URL of the #3 testimony.| -    | https://...
| `description_1` | Short description of who the person #1 is (Name, job title, etc.).| -    | Any text
| `description_2` | Short description of who the person #2 is (Name, job title, etc.).| -    | Any text
| `description_3` | Short description of who the person #3 is (Name, job title, etc.).| -    | Any text
| `quote_1` | A quote of the person #1.| -    | Any text
| `quote_2` | A quote of the person #2.| -    | Any text
| `quote_3` | A quote of the person #3.| -    | Any text


## Jobs
[![Jobs](docs/_static/homepage_widgets//jobs.png?raw=true)]()
```
<jobs
    rss_feed="https://www.publicjobs.ch/rss/~search1576049765b9fb8a630d17ec5dfcce06841a6e"
    jobs_card_title="Looking for ..."
    >
</jobs>
```
| Attribute Name | Description      | Value if left empty | Possible Values        |
| ------------- | -----------------| ------------------- | ---------------------- |
| `imrss_feedage_1`   | URL of the rss Feed for the job openings.| Cannot be left empty *    | https://...
| `jobs_card_title`   | Title of the card containing the job listings.| -    | Any text

\* Jobs widget will not be displayed if this value is missing.
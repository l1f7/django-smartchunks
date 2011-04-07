This library is basically fork from django-chunks but with few improvements.

Biggest feature is that added possibility to bind chunks to particular objects
via Generic Relations.

Second feature is possibility to render any chunks by special "builder"
objects which can build any chunk by provided rules.

Third feature is cache of all of above - particular chunk, object-related
chunk or list of chunks for special object.


### Why would anyone want this? ###

Anyone have project where content consist from several parts like content
and custom column or some quote etc. It's easy to make with
django-smartchunks - you can write custom builder which may display
custom tweets or some part of your content etc.


### Template tags ###

 * `chunk`
    Arguments:
      - key
      - _cache_time_
 * `object_chunk`
    Arguments:
      - object
      - key
      - _cache_time_
      - _default_chunk_
 * `object_chunks_list`
      - object
      - context_name

For `object_chunk` you may specify `default_chunk` argument which will
display plain chunk in case if chunk with provided key for particular object
is not exist.


### Usage: ###

    {% load chunks %}
    <html>
      <head>
        <title>Test</title>
      </head>
      <body>
        <h1> Blah blah blah</h1>
        <div id="sidebar">
            ...
        </div>
        <div id="left">
            {% chunk "home_page_left" %}
        </div>
        <div id="right">
            {% chunk "home_page_right" %}
        </div>
        <div id="content">
            <blockquote>{% object_chunk content "quote" %}</blockquote>
            <p>{{ content.body }}</p>

            <div class="somedata">
                {% object_chunk content "quote" 0 %}
            </div>
        </div>
      </body>
    </html>


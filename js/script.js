(function ($) {
    'use strict';

    $(document).ready(function () {
        if ($(window).width() < 1199) {
            $('.navbar .dropdown-toggle').on('click', function (e) {
                $(this).siblings('.dropdown-menu, .dropdown-submenu').animate(
                    {
                        height: 'toggle',
                    },
                    300
                );
            });
        }

        // popupFix init
        function popupFix() {
            var vScrollWidth = window.innerWidth - $(document).width();

            function noBodyScroll() {
                $('body').css({
                    'padding-right': vScrollWidth + 'px',
                    'overflow-y': 'hidden',
                });
            }

            function doBodyScroll() {
                setTimeout(function () {
                    $('body').css({
                        'padding-right': 0,
                        'overflow-y': 'auto',
                    });
                }, 300);
            }

            var navbarToggler = $('.navbar-toggler');
            $(navbarToggler).on('click', function () {
                if (navbarToggler.attr('aria-expanded') === 'false') {
                    noBodyScroll();
                }
                if (navbarToggler.attr('aria-expanded') === 'true') {
                    doBodyScroll();
                }
            });
        }
        popupFix();

        // smoothScroll init
        function smoothScroll() {
            $('.smooth-scroll').click(function (event) {
                if (
                    location.pathname.replace(/^\//, '') ===
                        this.pathname.replace(/^\//, '') &&
                    location.hostname === this.hostname
                ) {
                    var target = $(this.hash);
                    target = target.length
                        ? target
                        : $('[name=' + this.hash.slice(1) + ']');
                    if (target.length) {
                        event.preventDefault();
                        $('html, body').animate(
                            {
                                scrollTop: target.offset().top,
                            },
                            300,
                            function () {
                                var $target = $(target);
                                $target.focus();
                                if ($target.is(':focus')) {
                                    return false;
                                } else {
                                    $target.attr('tabindex', '-1');
                                    $target.focus();
                                }
                            }
                        );
                    }
                }
            });
        }
        smoothScroll();

        // videoPopupInit
        function videoPopupInit() {
            var $videoSrc;
            $('.video-play-btn').click(function () {
                $videoSrc = $(this).data('src');
            });
            $('#videoModal').on('shown.bs.modal', function (e) {
                $('#showVideo').attr(
                    'src',
                    $videoSrc +
                        '?autoplay=1&amp;modestbranding=1&amp;showinfo=0'
                );
            });
            $('#videoModal').on('hide.bs.modal', function (e) {
                $('#showVideo').attr('src', $videoSrc);
            });
        }
        videoPopupInit();

        // get news from newsapi
        const newsapi_url = `https://bing-news-search1.p.rapidapi.com/news/search?q=${area}, UK Business News&freshness=Week&textFormat=Raw&safeSearch=Off`;
        const options = {
            method: 'GET',
            headers: {
                'X-BingApis-SDK': 'true',
                'X-RapidAPI-Key':
                    '05440042f4msh81dc06bc821f70fp1c5bffjsnfbca942f6471',
                'X-RapidAPI-Host': 'bing-news-search1.p.rapidapi.com',
            },
        };
        fetch(newsapi_url, options)
            .then((response) => response.json())
            .then((data) => {
                // Extract the articles from the response
                const articles = data.value.slice(0, 9);

                // Loop through the articles and display the headlines
                const newsContainer = document.getElementById('news_container');

                if (articles.length > 0) {
                    articles.forEach((news) => {
                        // Create the main div element
                        const signlePostDiv = document.createElement('div');
                        signlePostDiv.classList.add(
                            'single-blog-post',
                            'd-flex',
                            'align-items-center',
                            'mb-2'
                        );

                        // Create the post thumbnail div and image
                        const postThumbnailDiv = document.createElement('div');
                        postThumbnailDiv.classList.add('post-thumbnail');
                        const img = document.createElement('img');
                        img.src = news.image
                            ? news?.image?.thumbnail?.contentUrl
                            : 'images/placeholder-image.png';
                        img.alt = news.image
                            ? 'news image'
                            : 'News report icons created by Freepik - Flaticon';
                        img.classList.add('news-image');
                        postThumbnailDiv.appendChild(img);
                        signlePostDiv.appendChild(postThumbnailDiv);

                        // Create the post content div
                        const postContentDiv = document.createElement('div');
                        postContentDiv.classList.add('post-content');

                        // Create the news URL link
                        const newsUrlLink = document.createElement('a');
                        newsUrlLink.ref = 'nofollow';
                        newsUrlLink.href = news?.url;
                        newsUrlLink.classList.add('news-url');
                        newsUrlLink.target = '_blank';

                        // Create the news title
                        const newsTitle = document.createElement('h5');
                        newsTitle.classList.add('news-title');
                        newsTitle.textContent = news?.name;
                        newsUrlLink.appendChild(newsTitle);
                        postContentDiv.appendChild(newsUrlLink);

                        // Create the post meta div and its contents
                        const postMetaDiv = document.createElement('div');
                        postMetaDiv.classList.add('post-meta', 'mt-1');
                        const p = document.createElement('p');
                        const postSourceSpan = document.createElement('span');
                        postSourceSpan.classList.add('post-source');
                        postSourceSpan.textContent = news?.provider[0]?.name;
                        const onSpan = document.createElement('span');
                        onSpan.textContent = ' on ';
                        const postDateSpan = document.createElement('span');
                        postDateSpan.classList.add('post-date');
                        const publishDate = new Date(news?.datePublished);
                        const formattedDate = publishDate.toLocaleDateString(
                            'en-Us',
                            {
                                month: 'long',
                                day: 'numeric',
                                year: 'numeric',
                            }
                        );
                        postDateSpan.textContent = formattedDate;
                        p.appendChild(postSourceSpan);
                        p.appendChild(onSpan);
                        p.appendChild(postDateSpan);
                        postMetaDiv.appendChild(p);
                        postContentDiv.appendChild(postMetaDiv);
                        signlePostDiv.appendChild(postContentDiv);
                        // Append the created element to the body of the HTML document
                        newsContainer.appendChild(signlePostDiv);
                    });
                } else {
                    const noNews = document.createElement('p');
                    noNews.classList.add('text-danger');
                    noNews.textContent = 'No news articles found!';
                    newsContainer.appendChild(noNews);
                }
            })
            .catch((error) => console.error(error));
    });
})(jQuery);

(function ($) {
    'use strict';
    $.fn.incircle = function (options) {
        var settings = $.extend(
            {
                color: '#556b2f',
                backgroundColor: 'white',
                type: 1, //circle type - 1 whole, 0.5 half, 0.25 quarter
                radius: '14em', //distance from center
                start: 0, //shift start from 0
                top: '0',
                left: '0',
            },
            options
        );
        this.css({
            position: 'relative',
            top: settings.top,
            left: settings.left,
            'list-style-type': 'none',
            margin: 0,
        });
        var elements = this.children(':not(:first-child)');
        var numberOfElements =
            settings.type === 1 ? elements.length : elements.length - 1;
        var slice = (360 * settings.type) / numberOfElements;
        elements.each(function (i) {
            var $self = $(this),
                rotate = slice * i + settings.start,
                rotateReverse = rotate * -1;
            $self.css({
                position: 'absolute',
                '-webkit-transition': 'all 1s linear',
                '-moz-transition': 'all 1s linear',
                transition: 'all 1s linear',
            });
            $self.css({
                transform:
                    'rotate(' +
                    rotate +
                    'deg) translate(' +
                    settings.radius +
                    ') rotate(' +
                    rotateReverse +
                    'deg)',
            });
        });
        return this;
    };
})(jQuery);

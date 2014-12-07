import lxml.etree as et
import json, re, urllib

######################################################
# Here are some variables you can change.  Have fun! #
######################################################
cover_image_host        = 'covers.openlibrary.org'
cover_image_prefix      = 'b/ISBN/'
cover_image_suffix      = '-M.jpg'
cover_image_mime_type   = 'image/jpeg'
cover_image_default_url = 'http://lbcommuter.com/wp-content/uploads/2011/05/roadrunner.jpg'
num_items               = '60'
opac_host               = 'libcat.linnbenton.edu'
org_unit                = 'LBCCLIB'




ATOM_NAMESPACE = 'http://www.w3.org/2005/Atom'
ATOM = "{%s}" % ATOM_NAMESPACE
DC_NAMESPACE = 'http://purl.org/dc/elements/1.1/'
DC = "{%s}" % DC_NAMESPACE
HOLDINGS_NAMESPACE = 'http://open-ils.org/spec/holdings/v1'
HOLDINGS = "{%s}" % HOLDINGS_NAMESPACE
BOOK_VOLUME_XPATH = HOLDINGS + 'holdings/' + HOLDINGS + 'volumes/' + HOLDINGS + 'volume'
VOLUME_COPY_XPATH = HOLDINGS + 'copies/' + HOLDINGS + 'copy'
BOOK_COPY_XPATH = BOOK_VOLUME_XPATH + '/' + VOLUME_COPY_XPATH



feed_url = 'http://' + opac_host + '/opac/extras/browse/atom-full/item-age/' + org_unit + '/1/' + num_items

def check_location(entry):
	locations = book.findall(BOOK_COPY_XPATH + '/' + HOLDINGS + 'location')
	for location in locations:
		if 't' == location.get('opac_visible'):
			return True
	return False


def is_book_good(entry):
	if False == check_location(entry): return False
	return True

def is_cover_image_good(cover_image_url):
	response = urllib.urlopen(cover_image_url)
	headers = response.info()
	if 'Content-Type' in headers:
		if cover_image_mime_type == headers['Content-Type']:
			return True
	return False

original = et.parse(feed_url)
books = original.findall(ATOM + 'entry')

data = []
i = 0

for book in books:
	if is_book_good(book):
		data.append({})
		data[i]['label'] = book.find(ATOM + 'title').text.strip(' /')
		author = book.find(ATOM + 'author')
		if author is not None:
			data[i]['author'] = author.find(ATOM + 'name').text

		links = book.findall(ATOM + 'link')
		for link in links:
			if 'opac' == link.get('rel'):
				data[i]['uri'] = link.get('href')
				break

		data[i]['date-cataloged'] = book.find(ATOM + 'updated').text

		isbns = book.findall(DC + 'identifier')
		if not isbns:
			data[i]['cover-image'] = cover_image_default_url
		else:
			for isbn in isbns:
				url_substitution = (re.subn('URN.ISBN.([X0-9]{10,13}).*', 'http://' + cover_image_host + '/' + cover_image_prefix + r'\1' + cover_image_suffix, isbn.text))
				if 1 == url_substitution[1]:
					cover_image_url = url_substitution[0]
					if is_cover_image_good(cover_image_url):
						data[i]['cover-image'] = cover_image_url
						break
					data[i]['cover-image'] = cover_image_default_url

		volumes = book.findall(BOOK_VOLUME_XPATH)
		for volume in volumes:
			if org_unit == volume.get('lib'):
				data[i]['call-number'] = volume.get('label')
				data[i]['shelving-location'] = volume.find(VOLUME_COPY_XPATH + '/' + HOLDINGS + 'location').text
				break
		i = 1 + i

exhibit_data = {'items': data}
print json.dumps(exhibit_data)

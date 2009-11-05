"""
"""
import sys
import threading


class LockableDict:
	"""A dictionary with locking. 'nuff said
	
	Uses threading.Lock to make itself more thread safe.
	
	This dictionary is intended for use when multiple append/del/get actions will be 
	done by various threads.
    
	"""
	def __init__(self):
		self.__lock = threading.Lock()
		self.__dict = {}
	
	def __setitem__(self, key, value):
		self.__lock.acquire()
		try:
			self.__dict[key] = value
		except:
			self.__lock.release()
			raise
		self.__lock.release()
		
	def __getitem__(self, key):
		self.__lock.acquire()
		try:
			value = self.__dict[key]
		except:
			self.__lock.release()
			raise
		self.__lock.release()
		return value
	
	def __delitem__(self, key):
		self.__lock.acquire()
		try:
			del self.__dict[key]
		except:
			self.__lock.release()
			raise sys.exc_type, sys.exc_value
		self.__lock.release()

	def __len__(self):
		self.__lock.acquire()
		l = len(self.__dict)
		self.__lock.release()		
		return l
		
	def keys(self):
		self.__lock.acquire()
		try:
			keys = self.__dict.keys()
		except:
			self.__lock.release()
			raise
		self.__lock.release()
		return keys

	def values(self):
		self.__lock.acquire()
		try:
			values = self.__dict.values()
		except:
			self.__lock.release()
			raise
		self.__lock.release()
		return values		
	
	def has_key(self, key):
		self.__lock.acquire()
		try:
			result = self.__dict.has_key(key)
		except:
			self.__lock.release()
			raise
		self.__lock.release()
		return result
